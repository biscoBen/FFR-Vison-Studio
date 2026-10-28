-- Session-only walking encounters. Never changes equipment, skills, save data,
-- encounter groups, battle transitions, or the native map encounter flags.
local config = require('config')
if config.encounterToggle ~= 1 then return end
local runtime = {disabled=false, hooks={}}
_G.FFRStudioEncounterToggle = runtime
local current, original, text, layout, lastError, holdStart, held, painted = nil,nil,nil,nil,nil,nil,false,nil
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
local function remove_badge()
    if valid(text) then text:RemoveFromParent() end
    text,layout,painted=nil,nil,nil
end
local function restore()
    if valid(current) and original~=nil and current.m_OverwriteEncountRatio==0 then
        current.m_OverwriteEncountRatio=original
    end
    current,original=nil,nil
end
local function release()
    restore();remove_badge();holdStart,held=nil,false
end
local function context()
    local map=native('mucha.Default__CPP_BFL_Map')
    local actor=map:GetPlayerMapUnit()
    if not valid(actor) or not actor:IsA(native('mucha.CPP_MapUnit_Player')) then return end
    if map:IsDuringEncount() or native('mucha.Default__CPP_BFL_TalkEvent'):IsPlayingEvent()
        or not actor:IsEnableUnitInput() or actor:IsPaused() or not actor.m_IsEnableMovement
        or actor:GetMapMovementMethod()~=1 or actor:IsRidingRaft() then return end
    local systems=native('Engine.Default__SubsystemBlueprintLibrary')
    local input=systems:GetWorldSubsystem(actor,native('mucha.CPP_InputManager'))
    local menu=systems:GetWorldSubsystem(actor,native('mucha.CPP_MainMenuSubsystem'))
    if not valid(input) or not input:IsEnableInput() or not valid(menu)
        or menu:IsOpenMenu() or menu.bIsTransitioning then return end
    return actor,systems
end
local function canvas(root,depth)
    if not valid(root) or depth>10 then return end
    if root:IsA(native('UMG.CanvasPanel')) then return root end
    if root:IsA(native('UMG.UserWidget')) then
        local tree=root.WidgetTree
        return valid(tree) and canvas(tree.RootWidget,depth+1) or nil
    end
    if not root:IsA(native('UMG.PanelWidget')) then return end
    local count=root:GetChildrenCount()
    assert(count>=0 and count<128,'Unexpected field widget child count')
    for i=0,count-1 do
        local result=canvas(root:GetChildAt(i),depth+1)
        if result then return result end
    end
end
local function badge(actor)
    -- FieldWidgetManager derives from Object, not WorldSubsystem. Resolve its
    -- existing instance; never pass that class to GetWorldSubsystem.
    local controller=native('Engine.Default__GameplayStatics'):GetPlayerController(actor,0)
    local matches,fallback={},{}
    for _,manager in ipairs(FindAllOf('CPP_FieldWidgetManager') or {}) do
        if valid(manager) and not manager:GetFullName():find('Default__',1,true) then
            local owner=manager.LayoutWidget
            if valid(owner) and owner:IsVisible() then
                local player=owner:GetOwningPlayer()
                if same(player,controller) then matches[#matches+1]=owner
                elseif not valid(player) then fallback[#fallback+1]=owner end
            end
        end
    end
    local owner=#matches==1 and matches[1] or (#matches==0 and #fallback==1 and fallback[1] or nil)
    if not valid(owner) then return false end
    if not same(owner,layout) then remove_badge() end
    if valid(text) then return true end
    local tree=owner.WidgetTree
    if not valid(tree) then return false end
    local panel=canvas(tree.RootWidget,0)
    if not valid(panel) then return false end
    -- A real UMG child, not PrintString (which shipping builds can suppress).
    local widget=StaticConstructObject(native('UMG.TextBlock'),tree)
    assert(valid(widget),'Could not construct encounter status text')
    local slot=panel:AddChildToCanvas(widget)
    if not valid(slot) then return false end
    text,layout=widget,owner -- Native panel/slot references retain it across GC.
    slot:SetAnchors({Minimum={X=0,Y=1},Maximum={X=0,Y=1}})
    slot:SetAlignment({X=0,Y=1});slot:SetPosition({X=24,Y=-24});slot:SetAutoSize(true)
    local font=widget.Font;font.Size=18
    widget:SetFont(font);widget:SetShadowOffset({X=1,Y=1})
    widget:SetShadowColorAndOpacity({R=0,G=0,B=0,A=1})
    widget:SetVisibility(3) -- HitTestInvisible: never intercept field/menu input.
    return true
end
local function paint()
    if painted==runtime.disabled then return end
    text:SetText('Random encounters: '..(runtime.disabled and 'OFF' or 'ON')..'\nF7 / Hold LT+RT (L2+R2)')
    text:SetColorAndOpacity({SpecifiedColor=runtime.disabled and {R=1,G=.8,B=.3,A=1}
        or {R=.65,G=1,B=.75,A=1},ColorUseRule=0})
    painted=runtime.disabled
end
local function toggle()
    runtime.disabled=not runtime.disabled
    log('Random encounters: '..(runtime.disabled and 'OFF' or 'ON (normal game rules)'))
end
local function update(keypress)
    local actor,systems=context()
    if not actor then release();return end
    -- Refuse a hidden toggle if the status display is not ready yet.
    if not badge(actor) then
        restore();assert(false,'Waiting for field HUD canvas; encounter control remains unchanged')
    end
    local gameplay=native('Engine.Default__GameplayStatics')
    local controller=gameplay:GetPlayerController(actor,0)
    if valid(controller) then
        local left=controller:GetInputAnalogKeyState({KeyName=FName('Gamepad_LeftTriggerAxis')})
        local right=controller:GetInputAnalogKeyState({KeyName=FName('Gamepad_RightTriggerAxis')})
        local now=gameplay:GetTimeSeconds(actor)
        if left>=.8 and right>=.8 then
            if not holdStart or now<holdStart then holdStart=now end
            if not held and now-holdStart>=1 then held=true;toggle() end
        else holdStart,held=nil,false end
    else holdStart,held=nil,false end
    if keypress then toggle() end
    if runtime.disabled then
        if not same(current,actor) then restore();current=actor end
        local value=actor.m_OverwriteEncountRatio
        assert(type(value)=='number' and value==value and math.abs(value)<1e12,'Invalid native walking encounter ratio')
        if original==nil or value~=0 then
            original=value
            log('Native walking encounter override: '..tostring(value)..' -> 0')
        end
        actor.m_OverwriteEncountRatio=0
    else restore() end
    paint()
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
for _,path in ipairs({'/Script/mucha.CPP_MapUnit_Playable:InputInteract',
    '/Script/mucha.CPP_BFL_TalkEvent:PlayEvent','/Script/mucha.CPP_MapTransitionTrigger:ExecuteTransition',
    '/Script/mucha.CPP_MapManager:Encount'}) do
    if valid(StaticFindObject(path)) then
        local callback=function() pcall(release) end
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
