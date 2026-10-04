-- Verified against the user's UE5.6 native SDK. Cosmetic only: no save setters,
-- actor respawn, party reorder, movement/collision/camera or story flag writes.
local config = require("config")
local current, chosen, originalIndex, appliedIndex = nil, nil, nil, nil
local changing, active, queued = false, false, false
local lastCycle = -1
local function valid(object) return object ~= nil and object:IsValid() end
local function log(message) print("[FFR field leader] " .. message .. "\n") end
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
    if not ok then fail(error) end
end
local function context()
    local map = library("mucha.Default__CPP_BFL_Map")
    local actor = map:GetPlayerMapUnit()
    if not valid(actor) or not actor:IsA(library("mucha.CPP_MapUnit_Player")) then return nil end
    local slots = config.actors[tostring(actor:GetMapUnitId())]
    if not slots or actor:GetMapMovementMethod() ~= 1 or actor:IsRidingRaft()
        or not actor:IsEnableUnitInput() or actor:IsPaused() or not actor.m_IsEnableMovement
        or map:IsDuringEncount() or library("mucha.Default__CPP_BFL_TalkEvent"):IsPlayingEvent() then return nil end
    local subsystems = library("Engine.Default__SubsystemBlueprintLibrary")
    local input = subsystems:GetWorldSubsystem(actor, library("mucha.CPP_InputManager"))
    local menu = subsystems:GetWorldSubsystem(actor, library("mucha.CPP_MainMenuSubsystem"))
    if not valid(input) or not input:IsEnableInput() or not valid(menu) or menu:IsOpenMenu()
        or menu.bIsTransitioning then return nil end
    -- Some builds expose UnitL1 without binding it. Connect the existing field
    -- action to its native receiver only when absent; never replace a binding.
    if not input:IsBound("UnitL1") then
        input:BindAction(1, "UnitL1", 1, true, actor, FName("InputL1"))
    end
    local party = library("mucha.Default__CPP_BFL_SaveDataParty")
    local count = party:GetPartyMax()
    assert(count >= 0 and count <= 8, "Unexpected active party slot count")
    local ids, seen = {}, {}
    for i = 0, count - 1 do
        local id = party:GetPartyUnitIdFromIndex(i)
        if slots[tostring(id)] and not seen[id] then ids[#ids + 1] = id; seen[id] = true end
    end
    return {actor = actor, slots = slots, ids = ids}
end
local function update(cycle, source)
    local c = context()
    if not c then restore(); return end
    if source and not same(source, c.actor) then return end
    if not same(current, c.actor) then
        restore(); current = c.actor; originalIndex = 0; appliedIndex = nil
    end
    -- Story costumes/special animation slots belong entirely to the game.
    local index = current.m_AnimationAssetIndex
    if index ~= originalIndex and index ~= appliedIndex then return end
    local selected
    for i, id in ipairs(c.ids) do if id == chosen then selected = i; break end end
    if cycle then
        local time = library("Engine.Default__GameplayStatics"):GetTimeSeconds(current)
        if time >= lastCycle and time - lastCycle < 0.2 then return end
        lastCycle = time
        if #c.ids == 0 then restore(); chosen = nil; return end
        if not selected then
            local nativeId = 1000 + current:GetMapUnitId() // 10
            for i, id in ipairs(c.ids) do if id == nativeId then selected = i; break end end
        end
        chosen = c.ids[((selected or 0) % #c.ids) + 1]
        log("Walking appearance: party unit " .. chosen)
    elseif not selected then
        restore(); chosen = nil; return
    end
    local target = c.slots[tostring(chosen)]
    if target and target ~= current.m_AnimationAssetIndex then
        setAsset(current, target, true); appliedIndex = target
    end
end
local function hook(path, pre, post)
    assert(valid(StaticFindObject(path)), "Native hook unavailable: " .. path)
    RegisterHook(path, pre, post or function() end)
end
local ok, error = pcall(function()
    assert(config.schema == 1, "Unsupported field leader bank")
    -- UnitL1 is released by the native LB/L1 input action. This callback stays
    -- on the game thread and never binds over battle/menu/cutscene controls.
    hook("/Script/mucha.CPP_MapUnit_Playable:InputL1", function() end, function(context)
        guarded(function() update(true, context:get()) end)
    end)
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
    RegisterKeyBind(Key.F6, function()
        ExecuteInGameThread(function() guarded(function() update(true) end) end)
    end)
    active = true
    LoopAsync(150, function()
        if not active then return true end
        if not queued then
            queued = true
            ExecuteInGameThread(function() queued = false; guarded(function() update(false) end) end)
        end
        return false
    end)
    log("Ready. LB/L1 or F6 cycles the active party while freely walking.")
end)
if not ok then fail(error) end
