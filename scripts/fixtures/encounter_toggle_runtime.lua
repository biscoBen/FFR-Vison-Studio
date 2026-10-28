-- Native API doubles: exercise the emitted runtime without inventing a save,
-- passive, equipment or encounter-start API. Real in-game behavior is a playtest.
clock=0; messages={};keys={};hooks={};loops={};event=false;menuOpen=false;inBattle=false
local function obj(o)
    o=o or {};o.valid=true
    function o:IsValid() return self.valid end
    function o:GetFullName() return self.name or tostring(self) end
    function o:IsA(class) return self.class==class or (self.panel and class==classes['UMG.PanelWidget']) end
    return o
end
classes={}
for _,n in ipairs({'mucha.CPP_MapUnit_Player','mucha.CPP_InputManager','mucha.CPP_MainMenuSubsystem',
    'mucha.CPP_FieldWidgetManager','UMG.CanvasPanel','UMG.PanelWidget','UMG.TextBlock','UMG.UserWidget'}) do classes[n]=obj({name=n}) end
function new_actor(name,ratio)
    local a=obj({name=name,class=classes['mucha.CPP_MapUnit_Player'],m_OverwriteEncountRatio=ratio,
        m_IsEnableMovement=true,input=true,vehicle=false,paused=false})
    function a:IsEnableUnitInput() return self.input end
    function a:IsPaused() return self.paused end
    function a:GetMapMovementMethod() return self.vehicle and 2 or 1 end
    function a:IsRidingRaft() return false end
    return a
end
actor=new_actor('Rain_A',-1)
controller=obj({left=0,right=0})
function controller:GetInputAnalogKeyState(key)
    assert(type(key.KeyName)=='string');return key.KeyName=='Gamepad_LeftTriggerAxis' and self.left or self.right
end
function new_hud()
    local p=obj({name='canvas',class=classes['UMG.CanvasPanel'],panel=true,children={obj({name='nativeQuestWidget'})}})
    function p:AddChildToCanvas(widget)
        self.children[#self.children+1]=widget;widget.parent=self
        local s=obj({})
        function s:SetAnchors(a) self.anchors=a end
        function s:SetAlignment(a) self.alignment=a end
        function s:SetPosition(a) self.position=a end
        function s:SetAutoSize(a) self.auto=a end
        return s
    end
    return obj({WidgetTree=obj({RootWidget=p}),IsVisible=function() return true end,
        GetOwningPlayer=function() return controller end}),p
end
hud,panel=new_hud()
local manager=obj({});local input=obj({})
function input:IsEnableInput() return true end
local menu=obj({bIsTransitioning=false})
function menu:IsOpenMenu() return menuOpen end
local systems=obj({})
function systems:GetWorldSubsystem(a,c)
    assert(a==actor)
    if c==classes['mucha.CPP_InputManager'] then return input end
    if c==classes['mucha.CPP_MainMenuSubsystem'] then return menu end
    error('Only real WorldSubsystem classes may be queried')
end
function FindAllOf(class)
    assert(class=='CPP_FieldWidgetManager');manager.LayoutWidget=hud;return {manager}
end
local gameplay=obj({})
function gameplay:GetPlayerController(a,i) assert(a==actor and i==0);return controller end
function gameplay:GetTimeSeconds(a) assert(a==actor);return clock end
local map=obj({})
function map:GetPlayerMapUnit() return actor end
function map:IsDuringEncount() return inBattle end
local talk=obj({})
function talk:IsPlayingEvent() return event end
local libs={['mucha.Default__CPP_BFL_Map']=map,['mucha.Default__CPP_BFL_TalkEvent']=talk,
    ['Engine.Default__SubsystemBlueprintLibrary']=systems,['Engine.Default__GameplayStatics']=gameplay}
function StaticFindObject(p) local n=p:gsub('^/Script/','');return libs[n] or classes[n] or obj() end
function StaticConstructObject(c,outer)
    assert(c==classes['UMG.TextBlock'] and outer==hud.WidgetTree)
    local t=obj({Font={Size=24},class=c})
    function t:SetText(s) self.label=s end
    function t:SetColorAndOpacity(c) self.color=c end
    function t:SetFont(f) self.Font=f end
    function t:SetShadowOffset(o) self.shadow=o end
    function t:SetShadowColorAndOpacity(c) self.shadowColor=c end
    function t:SetVisibility(v) assert(v==3) end
    function t:RemoveFromParent()
        for i,v in ipairs(self.parent.children) do if v==self then table.remove(self.parent.children,i);break end end
        self.removed=true
    end
    lastText=t;return t
end
function FName(n) return n end
Key={F7=118}
function RegisterKeyBind(k,cb) keys[k]=cb end
function RegisterHook(p,pre,post) hooks[p]={pre,post} end
function ExecuteInGameThread(cb) cb() end
function LoopAsync(ms,cb) loops[ms]=cb end
function print(s) messages[#messages+1]=s end
package.preload.config=function() return {schema=1,encounterToggle=1} end
function tick(dt) clock=clock+(dt or .1);FFRStudioEncounterToggle.tick() end
function press() keys[Key.F7]() end
function tests()
    tick();assert(actor.m_OverwriteEncountRatio==-1 and #panel.children==2)
    assert(lastText.label:find('ON') and lastText.Font.Size==18)
    press();assert(actor.m_OverwriteEncountRatio==0 and lastText.label:find('OFF'))
    collectgarbage('collect');tick();assert(actor.m_OverwriteEncountRatio==0)
    press();assert(actor.m_OverwriteEncountRatio==-1 and lastText.label:find('ON'))
    -- Hold both analog triggers for a full second, then toggle only once until release.
    controller.left,controller.right=1,1;tick(.1);tick(.9)
    assert(not FFRStudioEncounterToggle.disabled)
    tick(.11);assert(FFRStudioEncounterToggle.disabled)
    tick(3);assert(FFRStudioEncounterToggle.disabled)
    controller.left=0;tick();controller.left=1;tick();tick(1.1)
    assert(not FFRStudioEncounterToggle.disabled)
    controller.left,controller.right=0,0;tick()
    -- Context guards refuse toggles and return only our value to native control.
    press();local oldText=lastText
    for _,flag in ipairs({'event','menuOpen','inBattle'}) do
        _G[flag]=true;press();assert(actor.m_OverwriteEncountRatio==-1 and oldText.removed)
        assert(FFRStudioEncounterToggle.disabled)
        _G[flag]=false;tick();assert(actor.m_OverwriteEncountRatio==0);oldText=lastText
    end
    -- Native zone updates are preserved when normal encounters resume.
    actor.m_OverwriteEncountRatio=.5;tick();press();assert(actor.m_OverwriteEncountRatio==.5)
    press();actor.m_OverwriteEncountRatio=.25;press();assert(actor.m_OverwriteEncountRatio==.25)
    -- Transition hook restores before a boss/scripted fight; it never cancels it.
    press();local h=hooks['/Script/mucha.CPP_MapManager:Encount'];h[1]();h[2]()
    assert(actor.m_OverwriteEncountRatio==.25 and FFRStudioEncounterToggle.disabled)
    -- Each new actor/map and HUD owns separate state, with no dangling old widget.
    local old=actor;actor=new_actor('Rain_B',.75);hud,panel=new_hud();tick()
    assert(old.m_OverwriteEncountRatio==.25 and actor.m_OverwriteEncountRatio==0)
    assert(#panel.children==2 and lastText.label:find('OFF'))
    press();assert(actor.m_OverwriteEncountRatio==.75)
    -- Missing HUD refuses invisible toggles and leaves native encounters alone.
    local good=hud;hud=nil;press();assert(actor.m_OverwriteEncountRatio==.75)
    assert(not FFRStudioEncounterToggle.disabled);hud=good;tick()
    assert(#panel.children==2 and lastText.label:find('ON'))
    -- A later native/other-mod change is never replaced by a stale snapshot.
    press();actor.m_OverwriteEncountRatio=.33;inBattle=true;tick()
    assert(actor.m_OverwriteEncountRatio==.33)
    inBattle=false
    -- Native queued callbacks can be weak, including after a delayed request.
    local weak=setmetatable({}, {__mode='v'})
    ExecuteInGameThread=function(fn) weak.callback=fn end
    for i=1,45 do FFRStudioEncounterToggle.async() end
    collectgarbage('collect')
    assert(type(weak.callback)=='function');weak.callback()
end
