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
        m_EncountThresholdDistance=1200,m_IsEnableMovement=true,input=true,vehicle=false,paused=false})
    function a:IsEnableUnitInput() return self.input end
    function a:IsPaused() return self.paused end
    function a:GetMapMovementMethod() return self.vehicle and 2 or 1 end
    function a:IsRidingRaft() return false end
    local distance=a.m_EncountThresholdDistance;a.m_EncountThresholdDistance=nil
    setmetatable(a,{
        __index=function(_,key) if key=='m_EncountThresholdDistance' then return distance end end,
        __newindex=function(self,key,value)
            if key=='m_EncountThresholdDistance' then distance=string.unpack('f',string.pack('f',value))
            else rawset(self,key,value) end
        end,
    })
    return a
end
actor=new_actor('Rain_A',-1)
controller=obj({left=0,right=0})
function controller:GetInputAnalogKeyState(key)
    assert(type(key.KeyName)=='string');return key.KeyName=='Gamepad_LeftTriggerAxis' and self.left or self.right
end
viewport={};canCreate=true;created=0
function new_hud() return obj(),{children={obj({name='nativeQuestWidget'})}} end
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
function gameplay:GetRealTimeSeconds(a) assert(a==actor);return clock end
local map=obj({})
function map:GetPlayerMapUnit() return actor end
function map:IsDuringEncount() return inBattle end
local talk=obj({})
function talk:IsPlayingEvent() return event end
local libs={['mucha.Default__CPP_BFL_Map']=map,['mucha.Default__CPP_BFL_TalkEvent']=talk,
    ['Engine.Default__SubsystemBlueprintLibrary']=systems,['Engine.Default__GameplayStatics']=gameplay}
function StaticFindObject(p)
    if p:find('/Script/',1,true)~=1 then return nil end
    local n=p:gsub('^/Script/','');return libs[n] or classes[n] or obj()
end
local factory=obj()
local guideClass=obj({name='WBP_KeyGuide_C'})
libs['UMG.Default__WidgetBlueprintLibrary']=factory
function LoadAsset(path)
    assert(path=='/Game/UI/MainMenu/Common/Key/KeyGuide/WBP_KeyGuide.WBP_KeyGuide_C')
    return guideClass
end
function StaticConstructObject() error('Raw UWidget construction is forbidden') end
function factory:Create(context,c,player)
    assert(context==actor and c==guideClass and player==controller)
    if not canCreate then return nil end
    created=created+1
    local function part()
        local p=obj({visibility=1,opacity=0})
        function p:SetVisibility(value) self.visibility=value end
        function p:SetRenderOpacity(value) self.opacity=value end
        return p
    end
    local label=part()
    function label:SetText(s)
        assert(type(s)=='table' and s.nativeType=='FText','Native FText input required')
        self.label=s.value
    end
    local t=part();t.Text_Name=label;t.WBP_DirectionGridPanel=obj();t.Horizontal_Content=part()
    function t.WBP_DirectionGridPanel:SetVisibility(v) assert(v==1) end
    function t:AddToViewport(z) assert(z==50);viewport[#viewport+1]=self end
    function t:SetAnchorsInViewport(a) self.anchors=a end
    function t:SetAlignmentInViewport(a) self.alignment=a end
    function t:SetPositionInViewport(p,dpi)
        assert(not failPosition,'Fixture HUD positioning error')
        self.position=p;assert(dpi==false)
    end
    function t:SetDesiredSizeInViewport(size) assert(size.X==520 and size.Y==40) end
    function t:RemoveFromParent()
        for i,v in ipairs(viewport) do if v==self then table.remove(viewport,i);break end end
        self.removed=true
    end
    lastText=label;lastWidget=t;return t
end
function FName(n) return n end
function FText(value) assert(type(value)=='string');return {nativeType='FText',value=value} end
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
    event=true;tick();assert(created==0 and #viewport==0)
    event=false;tick();assert(actor.m_OverwriteEncountRatio==-1 and #panel.children==1 and #viewport==1)
    assert(lastText.label:find('ON') and lastWidget.position.Y==-24)
    for _,part in ipairs({lastWidget,lastWidget.Horizontal_Content,lastText}) do
        assert(part.visibility==3 and part.opacity==1,'Reveal native hidden guide content')
    end
    press();assert(actor.m_OverwriteEncountRatio==0 and lastText.label:find('OFF'))
    assert(actor.m_EncountThresholdDistance>1e20)
    collectgarbage('collect');tick();assert(actor.m_OverwriteEncountRatio==0)
    press();assert(actor.m_OverwriteEncountRatio==-1 and lastText.label:find('ON'))
    assert(actor.m_EncountThresholdDistance==1200)
    -- A native zone update can reset both fields between polling ticks.
    press();actor.m_OverwriteEncountRatio=.6;actor.m_EncountThresholdDistance=850
    hooks['/Script/mucha.CPP_MapUnit_Playable:InputMove'][1]()
    assert(actor.m_OverwriteEncountRatio==0 and actor.m_EncountThresholdDistance>1e20)
    press();assert(actor.m_OverwriteEncountRatio==.6 and actor.m_EncountThresholdDistance==850)
    -- Preserve a later native/other-mod change rather than restoring stale data.
    press();actor.m_EncountThresholdDistance=740;event=true;tick()
    assert(actor.m_EncountThresholdDistance==740)
    event=false;tick();press();assert(actor.m_EncountThresholdDistance==740)
    press();actor.m_EncountThresholdDistance=2e30;local changed=actor.m_EncountThresholdDistance
    event=true;tick();assert(actor.m_EncountThresholdDistance==changed)
    event=false;actor.m_EncountThresholdDistance=740;tick();press()
    actor.m_OverwriteEncountRatio=-1
    -- Hold both analog triggers for a full second, then toggle only once until release.
    controller.left,controller.right=1,1;tick(.1);tick(.9)
    assert(not FFRStudioEncounterToggle.disabled)
    tick(.11);assert(FFRStudioEncounterToggle.disabled)
    tick(3);assert(FFRStudioEncounterToggle.disabled)
    controller.left=0;tick();controller.left=1;tick();tick(1.1)
    assert(not FFRStudioEncounterToggle.disabled)
    controller.left,controller.right=0,0;tick()
    -- Context guards refuse toggles and return only our value to native control.
    press();local oldText=lastWidget
    for _,flag in ipairs({'event','menuOpen','inBattle'}) do
        _G[flag]=true;press();assert(actor.m_OverwriteEncountRatio==-1 and oldText.removed)
        assert(FFRStudioEncounterToggle.disabled)
        _G[flag]=false;tick();assert(actor.m_OverwriteEncountRatio==0);oldText=lastWidget
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
    assert(#panel.children==1 and #viewport==1 and lastText.label:find('OFF'))
    press();assert(actor.m_OverwriteEncountRatio==.75)
    -- Missing HUD refuses invisible toggles and leaves native encounters alone.
    local good=controller;controller=nil;press();assert(actor.m_OverwriteEncountRatio==.75)
    assert(not FFRStudioEncounterToggle.disabled);controller=good;tick()
    assert(#panel.children==1 and #viewport==1 and lastText.label:find('ON'))
    -- A failed native-widget setup removes its own viewport entry before retry.
    event=true;tick();event=false;failPosition=true;tick()
    assert(#viewport==0 and actor.m_OverwriteEncountRatio==.75)
    failPosition=false;tick();assert(#viewport==1 and lastText.label:find('ON'))
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
