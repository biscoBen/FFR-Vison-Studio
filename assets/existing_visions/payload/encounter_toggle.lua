-- Session-only native Dragon Seal effects on map parameters. Never changes
-- equipment, learned skills, save data, encounter groups or battle transitions.
local config = require('config')
if config.encounterToggle ~= 1 then return end
local runtime = {disabled=false, hooks={}, effects={}}
_G.FFRStudioEncounterToggle = runtime
local display, lastError, holdStart, held, painted
local function valid(o)
    return o ~= nil and (type(o)=='userdata' or type(o)=='table') and o:IsValid()
end
local function native(name)
    local object=StaticFindObject('/Script/'..name)
    assert(valid(object),'Native object unavailable: '..name)
    return object
end
local function log(s) print('[FFR encounters] '..s..'\n') end
local function same(a,b) return valid(a) and valid(b) and a:GetFullName()==b:GetFullName() end
local function list(array)
    local values={}
    array:ForEach(function(_,value)
        if type(value.get)=='function' then value=value:get() end
        values[#values+1]=value
        assert(#values<=256,'Unexpected map effect array size')
    end)
    return values
end
local checked={}
local function signature(name,expected)
    if checked[name] then return end
    local fields={}
    native('mucha.'..name):ForEachProperty(function(p) fields[#fields+1]=p:GetFullName():match('^(%w+)') end)
    assert(table.concat(fields,',')==expected,'Unsupported native encounter signature: '..name)
    checked[name]=true
end
local function remove_badge()
    if display then display:remove() end
    display,painted=nil,nil
end
local function restore()
    for key,owned in pairs(runtime.effects) do
        if valid(owned.parameter) and valid(owned.effect) then
            local array=owned.parameter.m_ContEffectList
            local keep,found={},false
            for _,effect in ipairs(list(array)) do
                if same(effect,owned.effect) then found=true else keep[#keep+1]=effect end
            end
            if found then
                -- Pinned UE4SS TArray writes are 1-based and extend on append.
                -- Rebuild only after snapshotting; preserve every foreign effect.
                array:Empty()
                for index,effect in ipairs(keep) do array[index]=effect end
            end
        end
        runtime.effects[key]=nil
    end
    runtime.applied=nil
end
local function release(reason)
    if runtime.disabled and next(runtime.effects) then
        log('Releasing owned effects; reason='..tostring(reason or 'context/error'))
    end
    restore();remove_badge();holdStart,held=nil,false
end
local function context()
    local map=native('mucha.Default__CPP_BFL_Map')
    local actor=map:GetPlayerMapUnit()
    if not valid(actor) or not actor:IsA(native('mucha.CPP_MapUnit_Player')) then return nil,'Walking player not ready' end
    if map:IsDuringEncount() then return nil,'Encounter transition active' end
    if native('mucha.Default__CPP_BFL_TalkEvent'):IsPlayingEvent() then return nil,'Story event active' end
    if not actor:IsEnableUnitInput() then return nil,'Player input disabled' end
    if actor:IsPaused() then return nil,'Player paused' end
    if not actor.m_IsEnableMovement then return nil,'Player movement disabled' end
    if actor:GetMapMovementMethod()~=1 then return nil,'Movement method is not walking' end
    if actor:IsRidingRaft() then return nil,'Player riding raft' end
    local systems=native('Engine.Default__SubsystemBlueprintLibrary')
    local input=systems:GetWorldSubsystem(actor,native('mucha.CPP_InputManager'))
    local menu=systems:GetWorldSubsystem(actor,native('mucha.CPP_MainMenuSubsystem'))
    if not valid(input) or not input:IsEnableInput() then return nil,'World input disabled or unavailable' end
    if not valid(menu) then return nil,'Menu subsystem unavailable' end
    if menu:IsOpenMenu() or menu.bIsTransitioning then return nil,'Menu open or transitioning' end
    return actor,systems
end
local function badge(actor)
    local controller=native('Engine.Default__GameplayStatics'):GetPlayerController(actor,0)
    if display and (not display:valid() or not same(display.controller,controller) or not same(display.context,actor)) then remove_badge() end
    if not display then
        display=create_status_hud(actor,{anchorX=0,anchorY=1,x=24,y=-24})
    end
    return display~=nil and display:valid()
end
local function paint()
    display:show()
    if painted==runtime.disabled then return end
    display:set('Random encounters: '..(runtime.disabled and 'OFF' or 'ON')..'   F7 / Hold LT+RT (L2+R2)')
    painted=runtime.disabled
end
local function toggle()
    runtime.disabled=not runtime.disabled
    log('Random encounters: '..(runtime.disabled and 'OFF' or 'ON (normal game rules)'))
end
local function apply(actor)
    signature('CPP_BFL_Map:GetMapUnitParameter','IntProperty,ObjectProperty')
    signature('CPP_BFL_Skill:GetSkillEffectDataById','IntProperty,StructProperty')
    signature('CPP_BFL_Skill:CreateContEffect','ObjectProperty,ObjectProperty,StructProperty,IntProperty,BoolProperty,BoolProperty,ObjectProperty')
    local map=native('mucha.Default__CPP_BFL_Map')
    local skill=native('mucha.Default__CPP_BFL_Skill')
    local data=skill:GetSkillEffectDataById(71000)
    assert(data.ID==71000 and data.EffectType==192 and data.ParamList[1]==0,
        'The native Dragon Seal effect changed; encounter control was not applied')
    local seen,count={},0
    for id=1001,1008 do
        local parameter=map:GetMapUnitParameter(id)
        if valid(parameter) then
            assert(parameter:IsA(native('mucha.CPP_UnitParameter')) and
                not parameter:IsA(native('mucha.CPP_BtlUnitParameter')),'Expected a native map parameter')
            local key=parameter:GetFullName();seen[key]=true;count=count+1
            local array=parameter.m_ContEffectList
            local current=list(array);local owned=runtime.effects[key];local found,zero=false,false
            for _,effect in ipairs(current) do
                assert(valid(effect),'Invalid native map effect')
                if owned and same(effect,owned.effect) then found=true end
                local entry=effect:GetEffectData()
                if entry.EffectType==192 and entry.ParamList[1]==0 then zero=true end
            end
            if owned and not found then runtime.effects[key]=nil end
            if not zero then
                -- Use the game's effect factory and the actual native passive
                -- source (1052). This never equips or learns the passive.
                local effect=skill:CreateContEffect(parameter,parameter,data,1052,true,false)
                assert(valid(effect),'Native Dragon Seal effect could not be created')
                runtime.effects[key]={parameter=parameter,effect=effect}
                assert(effect:IsA(native('mucha.CPP_ContFxEncountRatio')) and
                    same(effect:GetTargetUnitParameter(),parameter),'Native Dragon Seal target did not bind')
                local attached=false
                for _,present in ipairs(list(array)) do if same(present,effect) then attached=true;break end end
                if not attached then array[array:GetArrayNum()+1]=effect end
            end
        end
    end
    assert(count>0,'No native map party parameters are ready')
    -- A party-cache replacement can leave an older parameter alive. Remove only
    -- our effect there, without touching the new cache or equipped Dragon Seal.
    local active=runtime.effects;local stale={}
    for key,owned in pairs(active) do if not seen[key] then stale[key]=owned;active[key]=nil end end
    if next(stale) then runtime.effects=stale;restore();runtime.effects=active end
    if runtime.applied~=count then log('Native Dragon Seal active on '..count..' map characters');runtime.applied=count end
end
runtime.snapshot=function(reason)
    log('Diagnostic '..tostring(reason)..'; requested OFF='..tostring(runtime.disabled)..'; last error='..tostring(lastError))
    for target,owned in pairs(runtime.effects) do
        log('Owned target='..target..'; effect='..(valid(owned.effect) and owned.effect:GetFullName() or 'invalid'))
    end
    local map=native('mucha.Default__CPP_BFL_Map');local actor=map:GetPlayerMapUnit()
    if valid(actor) then
        log('Actor='..actor:GetFullName()..'; walking method='..tostring(actor:GetMapMovementMethod())..
            '; override='..tostring(actor.m_OverwriteEncountRatio)..'; threshold='..tostring(actor.m_EncountThresholdDistance))
    end
    signature('CPP_BFL_Unit:GetPlayableUnitParameterObj','IntProperty,ObjectProperty')
    local units=native('mucha.Default__CPP_BFL_Unit')
    for id=1001,1008 do
        -- Compare the map cache with the ordinary playable-parameter getter.
        -- Read only; never attach an effect to a diagnostic/temporary object.
        local cached=map:GetMapUnitParameter(id)
        for _,source in ipairs(valid(cached) and {'map','playable'} or {}) do
            local parameter
            if source=='map' then parameter=cached else parameter=units:GetPlayableUnitParameterObj(id) end
            if valid(parameter) then
                local effects=list(parameter.m_ContEffectList);local seals={}
                for _,effect in ipairs(effects) do
                    if valid(effect) then
                        local data=effect:GetEffectData()
                        if data.EffectType==192 then
                            seals[#seals+1]=tostring(data.ID)..':'..tostring(data.ParamList[1])
                        end
                    end
                end
                log('Unit='..id..'; source='..source..'; object='..parameter:GetFullName()..
                    '; effects='..#effects..'; encounter effects='..table.concat(seals,','))
            end
        end
    end
end
local function diagnostic(reason)
    local ok,message=pcall(runtime.snapshot,reason)
    if not ok then log('Diagnostic unavailable: '..tostring(message)) end
end
local function update(keypress)
    local actor,systems=context()
    if not actor then
        if keypress then log('Toggle ignored outside free-walking context: '..tostring(systems)) end
        release('walking context unavailable');return
    end
    -- Refuse a hidden toggle if the status display is not ready yet.
    if not badge(actor) then
        restore();assert(false,'Waiting for field HUD canvas; encounter control remains unchanged')
    end
    local previous=runtime.disabled
    local gameplay=native('Engine.Default__GameplayStatics')
    local controller=gameplay:GetPlayerController(actor,0)
    if valid(controller) then
        local left=controller:GetInputAnalogKeyState({KeyName=FName('Gamepad_LeftTriggerAxis')})
        local right=controller:GetInputAnalogKeyState({KeyName=FName('Gamepad_RightTriggerAxis')})
        local now=gameplay:GetRealTimeSeconds(actor)
        if left>=.8 and right>=.8 then
            if not holdStart or now<holdStart then holdStart=now end
            if not held and now-holdStart>=1 then held=true;toggle() end
        else holdStart,held=nil,false end
    else holdStart,held=nil,false end
    if keypress then toggle() end
    if runtime.disabled then apply(actor) else restore();runtime.applied=nil end
    paint()
    if previous~=runtime.disabled then diagnostic('after toggle') end
end
local function guarded(keypress)
    local ok,message=pcall(update,keypress)
    if not ok then
        pcall(release)
        message=tostring(message)
        if lastError~=message then log(message) end
        lastError=message
    else lastError=nil end
    return false
end
runtime.tick=function() return guarded(false) end
runtime.key_action=function() guarded(true) end
runtime.key=function() ExecuteInGameThread(runtime.key_action) end
-- Root every callback: this loader can collect otherwise anonymous closures.
RegisterKeyBind(Key.F7,runtime.key)
-- Refresh map-parameter effects before walking after a party/cache change.
-- Never cancel Encount or change a movement threshold.
runtime.move=function()
    if not runtime.disabled then return end
    local ok,message=pcall(function()
        local actor=context()
        if actor then apply(actor) else restore() end
    end)
    if not ok then pcall(restore);log('Movement guard: '..tostring(message)) end
end
runtime.move_post=function() end
RegisterHook('/Script/mucha.CPP_MapUnit_Playable:InputMove',runtime.move,runtime.move_post)
for _,path in ipairs({'/Script/mucha.CPP_MapUnit_Playable:InputInteract',
    '/Script/mucha.CPP_BFL_TalkEvent:PlayEvent','/Script/mucha.CPP_MapTransitionTrigger:ExecuteTransition',
    '/Script/mucha.CPP_MapManager:Encount'}) do
    if valid(StaticFindObject(path)) then
        local callback=function(_,_,eventBattle)
            if path=='/Script/mucha.CPP_MapManager:Encount' and runtime.disabled then
                local ok,value=pcall(function() return eventBattle:get() end)
                log('Native battle entry while OFF; event battle='..(ok and tostring(value) or 'unavailable'))
                diagnostic('before native battle entry releases owned effects')
            end
            pcall(release,path)
        end
        local post=function() end
        runtime.hooks[#runtime.hooks+1]={callback,post}
        RegisterHook(path,callback,post)
    end
end
local nativeLoop=false
if type(LoopInGameThreadWithDelay)=='function' then
    nativeLoop=pcall(LoopInGameThreadWithDelay,100,runtime.tick)
end
if not nativeLoop then
    -- Reuse a rooted callback even if an old queue request arrives late.
    -- Replacing a per-request closure could leave a native weak reference nil.
    runtime.queued=function() runtime.pending=nil;runtime.tick() end
    runtime.async=function()
        if runtime.pending then
            runtime.pending=runtime.pending+1
            if runtime.pending<20 then return false end
        end
        runtime.pending=0
        if not pcall(ExecuteInGameThread,runtime.queued) then runtime.pending=nil end
        return false
    end
    LoopAsync(100,runtime.async)
end
log('Ready: F7 or hold both triggers for 1 second while walking. Encounters start ON each launch.')
