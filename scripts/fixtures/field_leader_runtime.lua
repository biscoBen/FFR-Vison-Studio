-- Executable integration fixture for UE4SS callback conventions and reflected
-- native signatures. The real asset bank is validated separately with the SDK.
hooks, keys, messages = {}, {}, {}
Key = {F6 = 117}
function FName(value) return {value = value} end
local function obj(value)
    value = value or {}; value.IsValid = function(self) return not self.invalid end
    return value
end
actor = obj({m_AnimationAssetIndex = 0, m_IsEnableMovement = true, input = true,
    m_AnimationName = {ToString = function() return 'move9' end}, id = 10,
    GetFullName = function(self) return 'Player' .. tostring(self.serial or 1) end,
    GetMapUnitId = function(self) return self.id end,
    GetMapMovementMethod = function(self) return self.vehicle and 3 or 1 end,
    IsRidingRaft = function(self) return self.raft or false end,
    IsEnableUnitInput = function(self) return self.input end,
    IsPaused = function(self) return self.paused or false end,
    IsA = function(self) return not self.vehicle end,
    PlayAnimation = function(self, name, same) assert(name == 'move9' and same) end})
local function context(value) return {get = function() return value end} end
actor.ChangeAnimationAsset = function(self, index)
    local h = hooks['/Script/mucha.CPP_Unit:ChangeAnimationAsset']
    if h then h[1](context(self)) end
    self.m_AnimationAssetIndex = index
end
party = {1001, 1002, 1003}
local maps = obj({GetPlayerMapUnit = function() return actor end,
    IsDuringEncount = function() return battle or false end})
local talks = obj({IsPlayingEvent = function() return event or false end})
local save = obj({GetPartyMax = function() return #party end,
    GetPartyUnitIdFromIndex = function(self, slot) return party[slot + 1] end})
input = obj({IsEnableInput = function() return not disabledInput end,
    IsBound = function(self, action) assert(action == 'UnitL1'); return self.bound or false end,
    BindAction = function(self, mapping, action, event, noDuplicate, receiver, name)
        assert(mapping == 1 and action == 'UnitL1' and event == 1 and noDuplicate)
        assert(receiver == actor and type(name) == 'table' and name.value == 'InputL1'); self.bound = true end})
menu = obj({IsOpenMenu = function() return inMenu or false end})
local inputClass, menuClass = obj(), obj()
local libs = {['mucha.Default__CPP_BFL_Map'] = maps,
    ['mucha.Default__CPP_BFL_TalkEvent'] = talks,
    ['mucha.Default__CPP_BFL_SaveDataParty'] = save,
    ['mucha.CPP_InputManager'] = inputClass, ['mucha.CPP_MainMenuSubsystem'] = menuClass,
    ['Engine.Default__SubsystemBlueprintLibrary'] = obj({GetWorldSubsystem = function(self, world, class)
        assert(world == actor); return class == inputClass and input or menu end}),
    ['Engine.Default__GameplayStatics'] = obj({GetTimeSeconds = function() return time end})}
function StaticFindObject(path) return libs[path:gsub('^/Script/', '')] or obj() end
function RegisterHook(path, pre, post) hooks[path] = {pre, post} end
function RegisterKeyBind(key, callback) keys[key] = callback end
function ExecuteInGameThread(callback) callback() end
function LoopAsync(ms, callback) tick = callback; assert(ms == 150) end
function print(message) messages[#messages + 1] = message end
package.preload.config = function()
    return {schema = 1, actors = {['10'] = {['1001'] = 5, ['1002'] = 6, ['1003'] = 7, ['1006'] = 10},
        ['60'] = {['1001'] = 4, ['1002'] = 5, ['1003'] = 6, ['1006'] = 9}}}
end
local function button()
    time = (time or 0) + 1
    local h = hooks['/Script/mucha.CPP_MapUnit_Playable:InputL1']; assert(h)
    h[1](context(actor)); h[2](context(actor))
end
function run_tests()
    -- The controller callback, not the keyboard callback, drives these checks.
    button(); assert(actor.m_AnimationAssetIndex == 6, 'First cycle must display Lasswell')
    button(); assert(actor.m_AnimationAssetIndex == 7)
    button(); assert(actor.m_AnimationAssetIndex == 5)
    for _, flag in ipairs({'battle', 'event', 'inMenu', 'disabledInput'}) do
        _G[flag] = true; button(); assert(actor.m_AnimationAssetIndex == 0, flag)
        _G[flag] = false; tick(); assert(actor.m_AnimationAssetIndex == 5)
    end
    actor.input = false; button(); assert(actor.m_AnimationAssetIndex == 0)
    actor.input = true; tick(); assert(actor.m_AnimationAssetIndex == 5)
    actor.vehicle = true; tick(); assert(actor.m_AnimationAssetIndex == 0)
    actor.vehicle = false; tick(); assert(actor.m_AnimationAssetIndex == 5)
    actor.raft = true; tick(); assert(actor.m_AnimationAssetIndex == 0)
    actor.raft = false; tick(); assert(actor.m_AnimationAssetIndex == 5)
    -- Restore before a native scene asset change; leave its index alone.
    actor:ChangeAnimationAsset(2); assert(actor.m_AnimationAssetIndex == 2)
    button(); tick(); assert(actor.m_AnimationAssetIndex == 2)
    actor:ChangeAnimationAsset(0); tick(); assert(actor.m_AnimationAssetIndex == 5)
    -- Immediately restore for interaction/event entry, without waiting for a tick.
    hooks['/Script/mucha.CPP_MapUnit_Playable:InputInteract'][1](context(actor))
    assert(actor.m_AnimationAssetIndex == 0); tick()
    hooks['/Script/mucha.CPP_BFL_TalkEvent:PlayEvent'][1](context(actor))
    assert(actor.m_AnimationAssetIndex == 0); tick()
    -- Party removal cannot leave the departed member as the walking appearance.
    party = {1002, 1003}; tick(); assert(actor.m_AnimationAssetIndex == 0)
    button(); assert(actor.m_AnimationAssetIndex == 6)
    party = {1002, 1002, 9999, 0, 1003}; button(); assert(actor.m_AnimationAssetIndex == 7)
    -- A newly created story player gets its own slot bank and original index.
    actor.serial = 2; actor.id = 60; actor.m_AnimationAssetIndex = 0; tick()
    assert(actor.m_AnimationAssetIndex == 6)
    time = time + 1; keys[Key.F6](); assert(actor.m_AnimationAssetIndex == 5)
    -- No supported party members: do not force an unavailable or old leader.
    party = {9999}; button(); assert(actor.m_AnimationAssetIndex == 0)
    assert(tick() == false)
end
