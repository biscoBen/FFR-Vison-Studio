-- Read-only esper observer. No hooks, setters, asset loads or summon commands.
-- In particular, do NOT call the hooked remaining-action/think getters: asking
-- those questions would run the mastery logic and change what we are measuring.
local PREFIX, INTERVAL, LIMIT = '[FFR Esper Trace] ', 100, 10000
local queued, stopped, lines, ticks, bookmark, forcePending = false, false, 0, 0, 0, false
local last, errors = {}, {}
local function emit(kind, fields)
    if lines >= LIMIT then return end
    lines = lines + 1
    print(PREFIX .. kind .. ' | ' .. table.concat(fields or {}, ' | ')
        .. ' | sample=' .. ticks .. '\n')
end
local function read(label, fn)
    local ok, result = pcall(fn)
    if ok then return result end
    if not errors[label] then
        errors[label] = true
        emit('READ_UNAVAILABLE', {label, tostring(result):gsub('[\r\n|]', ' '):sub(1, 240)})
    end
end
local function valid(o)
    return o ~= nil and (type(o) == 'userdata' or type(o) == 'table') and o:IsValid()
end
local function value(v) return v == nil and '?' or tostring(v) end
local function name(o) return valid(o) and o:GetFullName() or '-' end
local function field(o, key) return read('field:' .. key, function() return o[key] end) end
local function objects(class) return read('find:' .. class, function() return FindAllOf(class) end) or {} end
local function changed(seen, key, kind, fields, force)
    local text = table.concat(fields, ' | ')
    seen[key] = text
    if force or last[key] ~= text then emit(kind, fields) end
end
local function effects(parameter)
    return read('GetContEffectList', function()
        local ids = {}
        local list = parameter:GetContEffectList()
        local function add(effect)
            if valid(effect) then ids[#ids+1] = effect:GetEffectData().ID end
        end
        if type(list) == 'table' and type(list.ForEach) ~= 'function' then
            for _, effect in pairs(list) do add(effect) end
        elseif list then list:ForEach(function(_, wrapped) add(wrapped:get()) end) end
        table.sort(ids)
        return ids
    end)
end
local function passives(parameter)
    return read('GetPassiveSkillList', function()
        local ids = {}; local source = parameter:GetPassiveSkillList()
        local function add(id) if type(id) == 'number' then ids[#ids+1] = id end end
        if type(source) == 'table' and type(source.ForEach) ~= 'function' then
            for _, id in pairs(source) do add(id) end
        elseif source then source:ForEach(function(_, wrapped) add(wrapped:get()) end) end
        table.sort(ids); return ids
    end)
end
local function list(ids)
    if not ids then return '?' end
    local result = {}
    for i, id in ipairs(ids) do if i <= 200 then result[#result+1] = tostring(id) end end
    return table.concat(result, ',')
end
local function flags(ids)
    if not ids then return '?' end
    local found = {}; for _, id in ipairs(ids) do found[id] = true end
    return 'damage:' .. tostring(found[196000] == true)
        .. ',mp:' .. tostring(found[196100] == true)
        .. ',extraHP:' .. tostring(found[196200] == true)
        .. ',earlySpecial:' .. tostring(found[196300] == true)
end
local function parameter(actor)
    if valid(actor) then return read('GetUnitParameter', function() return actor:GetUnitParameter() end) end
end
local function unit(seen, actor, force)
    if not valid(actor) or name(actor):find('Default__', 1, true) then return end
    local p = parameter(actor)
    if not valid(p) then return end
    local id = p:GetUnitId()
    local role = id == 1003 and 'Fina' or (id >= 10451 and id <= 10459 and 'nativeEsper' or 'other')
    local key = name(actor) .. '@' .. value(read('GetAddress', function() return actor:GetAddress() end))
    local ai = read('GetUnitAI', function() return actor:GetUnitAI() end)
    local ids = effects(p)
    local passiveIds = passives(p)
    local owner = field(p, 'm_pVisionOwner')
    local ownerP = parameter(owner)
    local fields = {key, 'role=' .. role, 'unitId=' .. id,
        'relation=' .. value(read('GetRelation', function() return p:GetRelation() end)),
        'dead=' .. value(read('IsDead', function() return p:IsDead() end)),
        'HP=' .. value(read('GetHitPoint', function() return p:GetHitPoint() end)),
        'maxHP=' .. value(read('GetMaxHitPoint', function() return p:GetMaxHitPoint() end)),
        'MP=' .. value(read('GetMagicPoint', function() return p:GetMagicPoint() end)),
        'maxMP=' .. value(read('GetMaxMagicPoint', function() return p:GetMaxMagicPoint() end)),
        'actions=' .. value(read('GetActionCountInBattle', function() return p:GetActionCountInBattle() end)),
        'AI=' .. name(ai), 'selectedSkill=' .. value(valid(ai) and field(ai, 'm_SkillId') or nil),
        'visionOwner=' .. name(owner),
        'visionOwnerId=' .. value(valid(ownerP) and read('owner:GetUnitId', function() return ownerP:GetUnitId() end) or nil),
        'effectIds=' .. list(ids), 'activePassiveIds=' .. list(passiveIds),
        'equippedVision=' .. name(field(p, 'm_pVision'))}
    if role == 'Fina' then fields[#fields+1] = 'masteryMarkers=' .. flags(ids) end
    changed(seen, 'unit:' .. key, 'UNIT', fields, force)
end
local function job(seen, o, force)
    if not valid(o) or name(o):find('Default__', 1, true) then return end
    local actor = field(o, 'm_pActionUnit')
    local p = parameter(actor)
    if not valid(p) then return end
    local skill = field(o, 'm_pSkill')
    local ai = read('GetUnitAI', function() return actor:GetUnitAI() end)
    local fields = {name(o), 'actor=' .. name(actor), 'unitId=' .. p:GetUnitId(),
        'skillObject=' .. name(skill),
        'selectedSkill=' .. value(valid(ai) and field(ai, 'm_SkillId') or nil),
        'actions=' .. value(read('GetActionCountInBattle', function() return p:GetActionCountInBattle() end))}
    changed(seen, 'job:' .. name(o), 'SKILL_JOB', fields, force)
end
local function snapshot(force)
    local seen, count = {}, 0
    for _, actor in ipairs(objects('CPP_BtlUnit')) do
        read('unit observation', function() unit(seen, actor, force) end)
    end
    for key in pairs(seen) do if key:sub(1, 5) == 'unit:' then count = count + 1 end end
    if count > 0 then ticks = ticks + 1 end
    for _, o in ipairs(objects('CPP_BtlJobSkill')) do
        read('skill job observation', function() job(seen, o, force) end)
    end
    changed(seen, 'counts', 'COUNTS', {'battleUnits=' .. count}, force)
    for key in pairs(last) do if not seen[key] then emit('ENDED', {key}) end end
    last = seen
end
local function stop(reason)
    if stopped then return end
    emit('STOPPED', {reason})
    stopped = true
end
local function sample(force)
    if stopped then return end
    if queued then forcePending = forcePending or force; return end
    queued = true
    local ok, err = pcall(ExecuteInGameThread, function()
        queued = false
        if stopped then return end
        force = force or forcePending; forcePending = false
        if force then bookmark = bookmark + 1; emit('BOOKMARK', {'number=' .. bookmark}) end
        read('snapshot', function() snapshot(force) end)
        if lines >= LIMIT-1 or ticks >= 9000 then stop('15-minute battle/event limit') end
    end)
    if not ok then queued = false; read('game thread scheduling', function() error(err) end) end
end
if RegisterKeyBind and Key then
    read('F8 bookmark', function() RegisterKeyBind(Key.F8, function() sample(true) end) end)
    read('F9 stop', function() RegisterKeyBind(Key.F9, function() stop('F9') end) end)
end
emit('READY', {'schema=1', 'intervalMs=' .. INTERVAL,
    'read-only; no hooks; F8 snapshot; F9 stop; missing markers are not a diagnosis by themselves'})
LoopAsync(INTERVAL, function()
    if stopped then return true end
    sample(false)
    return false
end)
