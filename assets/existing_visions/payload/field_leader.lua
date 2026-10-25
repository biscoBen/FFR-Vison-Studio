-- Verified against the user's UE5.6 native SDK. Cosmetic only: no save setters,
-- actor respawn, party reorder, movement/collision/camera or story flag writes.
local config = require("config")
local cycling = config.cycling ~= 0
local current, chosen, originalIndex, appliedIndex = nil, nil, nil, nil
local changing, active, pending = false, false, nil
local lastCycle = -1
-- The user's loader can collect anonymous callback references held only by
-- its native registry. Keep all of this controller's callbacks rooted in Lua.
local runtime = {hooks = {}}
_G.FFRStudioFieldRuntime = runtime
local lastError, lastState, queueError = nil, nil, nil
local function valid(object)
    return object ~= nil and (type(object) == 'userdata' or type(object) == 'table') and object:IsValid()
end
local function log(message) print("[FFR field leader] " .. message .. "\n") end
local function status(message)
    if message ~= lastState then lastState = message; log(message) end
end
local function library(name)
    local object = StaticFindObject("/Script/" .. name)
    assert(valid(object), "Native object unavailable: " .. name)
    return object
end
local function actorKey(actor) return valid(actor) and actor:GetFullName() or nil end
local function same(a, b) return actorKey(a) ~= nil and actorKey(a) == actorKey(b) end
local function setAsset(actor, index, refresh)
    changing = true
    local ok, failure = pcall(function()
        local name = actor.m_AnimationName:ToString()
        actor:ChangeAnimationAsset(index)
        if refresh then actor:PlayAnimation(name, true) end
    end)
    changing = false
    if not ok then error(failure) end
end
local function restore()
    if valid(current) and appliedIndex and current.m_AnimationAssetIndex == appliedIndex then
        setAsset(current, originalIndex, true)
    end
    appliedIndex = nil
end
local function fail(error)
    active = false
    pcall(restore)
    log("Cycling disabled to preserve the game state: " .. tostring(error))
end
local function guarded(callback)
    if not active or changing then return end
    local ok, error = pcall(callback)
    if not ok then
        -- Missing/stale objects during title/load/map transitions must not
        -- disable the saved walking choice for the rest of the session.
        pcall(restore)
        local message = tostring(error)
        if message ~= lastError then log('Waiting to retry walking appearance: ' .. message) end
        lastError = message
    else lastError = nil end
end
local function context()
    local map = library("mucha.Default__CPP_BFL_Map")
    local actor = map:GetPlayerMapUnit()
    if not valid(actor) or not actor:IsA(library("mucha.CPP_MapUnit_Player")) then return nil, 'Waiting for field player' end
    local mapId = tostring(actor:GetMapUnitId())
    local slots = config.actors[mapId]
    if not slots then return nil, 'No saved walking appearance for map unit ' .. mapId end
    if actor:GetMapMovementMethod() ~= 1 or actor:IsRidingRaft() then return nil, 'Original appearance: vehicle' end
    if library("mucha.Default__CPP_BFL_TalkEvent"):IsPlayingEvent() then return nil, 'Original appearance: event' end
    if not actor:IsEnableUnitInput() or actor:IsPaused() or not actor.m_IsEnableMovement then
        return nil, 'Original appearance: field control suspended'
    end
    if map:IsDuringEncount() then return nil, 'Original appearance: encounter' end
    local subsystems = library("Engine.Default__SubsystemBlueprintLibrary")
    local input = subsystems:GetWorldSubsystem(actor, library("mucha.CPP_InputManager"))
    local menu = subsystems:GetWorldSubsystem(actor, library("mucha.CPP_MainMenuSubsystem"))
    if not valid(input) or not input:IsEnableInput() or not valid(menu) or menu:IsOpenMenu()
        or menu.bIsTransitioning then return nil, 'Original appearance: input/menu unavailable' end
    -- Some builds expose UnitL1 without binding it. Connect the existing field
    -- action to its native receiver only when absent; never replace a binding.
    if cycling and not input:IsBound("UnitL1") then
        input:BindAction(1, "UnitL1", 1, true, actor, FName("InputL1"))
    end
    local ids, seen = {}, {}
    if cycling then
        local party = library("mucha.Default__CPP_BFL_SaveDataParty")
        local count = party:GetPartyMax()
        assert(count >= 0 and count <= 8, "Unexpected active party slot count")
        for i = 0, count - 1 do
            local id = party:GetPartyUnitIdFromIndex(i)
            if slots[tostring(id)] and not seen[id] then ids[#ids + 1] = id; seen[id] = true end
        end
    end
    local fallback = (config.defaults or {})[mapId] or 0
    return {actor = actor, slots = slots, ids = ids, fallback = fallback}
end
local function update(cycle, source)
    if cycle and not cycling then return end
    local c, reason = context()
    if not c then restore(); status(reason); return end
    if source and not same(source, c.actor) then return end
    if not same(current, c.actor) then
        restore(); current = c.actor; originalIndex = 0; appliedIndex = nil
    end
    -- Story costumes/special animation slots belong entirely to the game.
    local index = current.m_AnimationAssetIndex
    if index ~= originalIndex and index ~= appliedIndex then status('Original appearance: native story slot ' .. tostring(index)); return end
    local selected
    for i, id in ipairs(c.ids) do if id == chosen then selected = i; break end end
    if cycle then
        local time = library("Engine.Default__GameplayStatics"):GetTimeSeconds(current)
        if time >= lastCycle and time - lastCycle < 0.2 then return end
        lastCycle = time
        if #c.ids > 0 and not selected then
            local nativeId = 1000 + current:GetMapUnitId() // 10
            for i, id in ipairs(c.ids) do if id == nativeId then selected = i; break end end
        end
        if #c.ids > 0 then
            chosen = c.ids[((selected or 0) % #c.ids) + 1]
            selected = ((selected or 0) % #c.ids) + 1
            log("Walking appearance: party unit " .. chosen)
        else chosen = nil end
    elseif not selected then
        chosen = nil
    end
    local target = chosen and c.slots[tostring(chosen)] or c.fallback
    if target == 0 then restore(); status('Original field appearance selected'); return end
    if target and target ~= current.m_AnimationAssetIndex then
        setAsset(current, target, true); appliedIndex = target
    end
    status('Walking appearance active: map unit ' .. tostring(current:GetMapUnitId()) .. ', slot ' .. tostring(target))
end
local function hook(path, pre, post)
    assert(valid(StaticFindObject(path)), "Native hook unavailable: " .. path)
    post = post or function() end
    runtime.hooks[#runtime.hooks + 1] = {pre, post}
    RegisterHook(path, pre, post)
end

runtime.tick = function()
    if not active then return true end
    guarded(function() update(false) end)
    return false
end

runtime.async = function()
    if not active then return true end
    if pending then
        pending.waits = pending.waits + 1
        if pending.waits < 20 then return false end
        if queueError ~= 'timeout' then log('Walking callback timed out; scheduling a fresh update') end
        queueError = 'timeout'
    end
    local request = {waits = 0}
    request.run = function()
        if pending ~= request then return end
        pending = nil; queueError = nil
        runtime.tick()
    end
    pending = request
    local ok, error = pcall(ExecuteInGameThread, request.run)
    if not ok then
        pending = nil
        local message = tostring(error)
        if queueError ~= message then log('Walking callback unavailable; retrying: ' .. message) end
        queueError = message
    end
    return false
end
local ok, error = pcall(function()
    assert(config.schema == 1, "Unsupported field leader bank")
    -- UnitL1 is released by the native LB/L1 input action. This callback stays
    -- on the game thread and never binds over battle/menu/cutscene controls.
    if cycling then
        hook("/Script/mucha.CPP_MapUnit_Playable:InputL1", function() end, function(context)
            guarded(function() update(true, context:get()) end)
        end)
    end
    hook("/Script/mucha.CPP_MapUnit_Playable:DisableUnitInput", function(context)
        guarded(function() if same(current, context:get()) then restore() end end)
    end)
    hook("/Script/mucha.CPP_Unit:ChangeAnimationAsset", function(context)
        guarded(function() if same(current, context:get()) then restore() end end)
    end)
    hook("/Script/mucha.CPP_MapUnit_Playable:InputInteract", function() guarded(restore) end)
    hook("/Script/mucha.CPP_BFL_TalkEvent:PlayEvent", function() guarded(restore) end)
    hook("/Script/mucha.CPP_MapTransitionTrigger:ExecuteTransition", function() guarded(restore) end)
    hook("/Script/mucha.CPP_MapManager:Encount", function() guarded(restore) end)
    if cycling then
        runtime.cycle = function() guarded(function() update(true) end) end
        runtime.key = function()
            ExecuteInGameThread(runtime.cycle)
        end
        RegisterKeyBind(Key.F6, runtime.key)
    end
    active = true
    local nativeLoop = false
    if type(LoopInGameThreadWithDelay) == 'function' then
        local started, error = pcall(LoopInGameThreadWithDelay, 150, runtime.tick)
        if started then nativeLoop = true; log('Using persistent game-thread walking loop')
        else log('Persistent walking loop unavailable; using recoverable callback bridge: ' .. tostring(error)) end
    end
    if not nativeLoop then LoopAsync(150, runtime.async) end
    log(cycling and "Ready. LB/L1 or F6 cycles the active party while freely walking."
        or "Ready. Saved field appearance includes idle; native characters return during events.")
end)
if not ok then fail(error) end
