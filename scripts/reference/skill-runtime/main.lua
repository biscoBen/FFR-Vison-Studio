-- Optional sampled observer for the existing UE4SS installation. No hooks,
-- native offsets, setters, asset loads or playback calls. All reads run on the
-- game thread. Missing reflection fields are reported rather than guessed.
local PREFIX = '[FFR Skill Trace] '
local INTERVAL, MAX_LINES, MAX_SECONDS = 100, 10000, 600
local queued, stopped, ticks, lines, inBattle = false, false, 0, 0, false
local last, readErrors = {}, {}
local function emit(kind, fields)
    if lines >= MAX_LINES or (lines >= MAX_LINES-1 and kind ~= 'STOPPED') then return end
    fields = fields or {}
    fields[#fields+1] = 'sample=' .. ticks
    print(PREFIX .. kind .. ' | ' .. table.concat(fields, ' | ') .. '\n')
    lines = lines + 1
end
local function safe(label, callback)
    local ok, result = pcall(callback)
    if ok then return result end
    if not readErrors[label] then
        readErrors[label] = true
        emit('READ_UNAVAILABLE', {label, tostring(result):gsub('[\r\n|]', ' '):sub(1, 240)})
    end
end
local function valid(o)
    return o ~= nil and (type(o) == 'table' or type(o) == 'userdata') and o:IsValid()
end
local function object_name(o)
    if valid(o) then return o:GetFullName() end
    return '-'
end
local function value(v)
    if v == nil then return '?' end
    if type(v) == 'string' or type(v) == 'number' or type(v) == 'boolean' then return tostring(v) end
    return v:ToString()
end
local function vector(v)
    return string.format('%.2f,%.2f,%.2f', v.X, v.Y, v.Z)
end
local function field(o, key)
    return safe('field:' .. key, function() return o[key] end)
end
local function each(array, callback)
    if array == nil then return end
    array:ForEach(function(_, wrapped) callback(wrapped:get()) end)
end
local function objects(class)
    return safe('find:' .. class, function() return FindAllOf(class) end) or {}
end
local function instance(o)
    return valid(o) and not o:GetFullName():find('Default__', 1, true)
end
local function changed(seen, key, kind, fields)
    local signature = table.concat(fields, ' | ')
    seen[key] = signature
    if last[key] ~= signature then emit(kind, fields) end
end
local function sequence(actor)
    if not valid(actor) then return '-' end
    return object_name(actor.LevelSequenceAsset)
end
local function unit(seen, actor)
    local sprite = actor.m_pSsPlayerComponent
    if not valid(sprite) then return false end
    local key = actor:GetFullName()
    local fields = {key, 'sprite=' .. object_name(sprite), 'project=' .. object_name(sprite.SsProject),
        'cachedMotion=' .. value(actor.m_AnimationName), 'visible=' .. tostring(actor.m_IsVisible)}
    local outputs = {}
    local names = safe('sprite:GetPlayingAnimationName', function()
        sprite:GetPlayingAnimationName(outputs, outputs)
        local result = {}
        for k,v in pairs(outputs) do result[#result+1] = tostring(k) .. '=' .. value(v) end
        table.sort(result)
        return table.concat(result, ',')
    end)
    fields[#fields+1] = 'playing=' .. (names or '?')
    local location = safe('unit:GetActorLocation', function() return vector(actor:K2_GetActorLocation()) end)
    fields[#fields+1] = 'position=' .. (location or '?')
    changed(seen, 'unit:' .. key, 'UNIT', fields)
    return true
end
local function job(seen, o, listName)
    if not instance(o) then return end
    local key = o:GetFullName()
    local skill = field(o, 'm_pSkill')
    local id = valid(skill) and safe('skill:GetSkillId', function() return skill:GetSkillId() end) or nil
    local fields = {key, 'list=' .. listName, 'skill=' .. object_name(skill), 'skillId=' .. value(id),
        'sequence=' .. sequence(field(o, 'm_pLevelSequenceActor')),
        'sound=' .. sequence(field(o, 'm_pSoundSequenceActor'))}
    local actors, targets = {}, {}
    each(field(o, 'm_ActionUnitList'), function(a) actors[#actors+1] = object_name(a) end)
    each(field(o, 'm_TargetUnitList'), function(a) targets[#targets+1] = object_name(a) end)
    table.sort(actors); table.sort(targets)
    fields[#fields+1] = 'actors=' .. table.concat(actors, ',')
    fields[#fields+1] = 'targets=' .. table.concat(targets, ',')
    changed(seen, 'job:' .. key .. ':' .. listName, 'JOB', fields)
    -- These lists establish a job/effect relationship, unlike mere time
    -- proximity of a globally active component. Snapshot both separately.
    each(field(o, 'm_GeneratedNiagaraDatas'), function(d)
        local component = d.NiagaraComponent
        local record = {key, 'id=' .. value(d.NiagaraID), 'component=' .. object_name(component)}
        if valid(component) then record[#record+1] = 'asset=' .. object_name(component.Asset) end
        changed(seen, 'jobfx:' .. key .. ':' .. object_name(component), 'JOB_NIAGARA', record)
    end)
    each(field(o, 'm_GeneratedSpriteStudioDatas'), function(d)
        local a = d.ssActor
        changed(seen, 'jobss:' .. key .. ':' .. object_name(a), 'JOB_SPRITE',
            {key, 'id=' .. value(d.spriteStudioID), 'actor=' .. object_name(a)})
    end)
end
local function snapshot()
    local seen, units = {}, {}
    for _, o in ipairs(objects('CPP_BtlUnit')) do
        safe('unit discovery', function()
            if instance(o) and valid(o.m_pSsPlayerComponent) then units[#units+1] = o end
        end)
    end
    if #units == 0 then
        if inBattle then emit('BATTLE_OBJECTS_ENDED') end
        inBattle = false; last = {}
        return
    end
    if not inBattle then emit('BATTLE_OBJECTS_FOUND') end
    inBattle = true; ticks = ticks + 1
    for _, o in ipairs(units) do safe('unit snapshot', function() unit(seen, o) end) end
    for _, manager in ipairs(objects('CPP_BtlJobManager')) do
        safe('job manager snapshot', function()
            if instance(manager) then
                for _, key in ipairs({'m_WorkingJobList', 'm_WaitingJobList'}) do
                    each(field(manager, key), function(o) safe('job snapshot', function() job(seen, o, key) end) end)
                end
            end
        end)
    end
    -- Include sequence actors not exposed in a reflected job list. A sampled
    -- active component/sequence is evidence of playback; its absence is not
    -- proof that it never played (very short events can fall between samples).
    for _, o in ipairs(objects('LevelSequenceActor')) do
        safe('sequence snapshot', function()
            if not instance(o) then return end
            local player = o:GetSequencePlayer()
            if valid(player) and player:IsPlaying() then
                changed(seen, 'sequence:' .. o:GetFullName(), 'SEQUENCE', {o:GetFullName(), sequence(o)})
            end
        end)
    end
    for _, o in ipairs(objects('NiagaraComponent')) do
        safe('Niagara snapshot', function()
            if instance(o) and o:IsActive() then
                changed(seen, 'fx:' .. o:GetFullName(), 'NIAGARA', {o:GetFullName(), 'asset=' .. object_name(o.Asset),
                    'owner=' .. object_name(o:GetOwner()), 'position=' .. vector(o:K2_GetComponentLocation())})
            end
        end)
    end
    for key in pairs(last) do if not seen[key] then emit('ENDED', {key}) end end
    last = seen
end
local function stop(reason)
    if stopped then return end
    -- Reserve room for a final marker even after the normal event cap.
    emit('STOPPED', {reason, 'events=' .. lines, 'battleSamples=' .. ticks})
    stopped = true
end
if RegisterKeyBind and Key then
    -- Optional observation bookmarks. Neither key invokes a game action.
    safe('bookmark key', function() RegisterKeyBind(Key.F8, function() if not stopped then emit('BOOKMARK') end end) end)
    safe('stop key', function() RegisterKeyBind(Key.F9, function() stop('F9') end) end)
end
emit('READY', {'schema=1', 'intervalMs=' .. INTERVAL, 'maxBattleSeconds=' .. MAX_SECONDS,
    'read-only polling; no hooks or playback changes; F8 bookmark; F9 stop'})
LoopAsync(INTERVAL, function()
    if stopped then return true end
    if not queued then
        queued = true
        ExecuteInGameThread(function()
            queued = false
            if stopped then return end
            safe('snapshot', snapshot)
            if lines >= MAX_LINES-1 or ticks*INTERVAL >= MAX_SECONDS*1000 then stop('capture limit') end
        end)
    end
    return false
end)
