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
    'mucha.CPP_FieldWidgetManager','mucha.CPP_UnitParameter','mucha.CPP_BtlUnitParameter',
    'mucha.CPP_ContFxEncountRatio','UMG.CanvasPanel','UMG.PanelWidget','UMG.TextBlock','UMG.UserWidget'}) do classes[n]=obj({name=n}) end
-- Actual pinned UE4SS TArray protocol: 1-based indexed writes extend, plus
-- GetArrayNum/ForEach/Empty. No invented AddEffect/equipment/save API.
function array(values)
    local a={}
    function a:GetArrayNum() return #values end
    function a:ForEach(fn) for i,v in ipairs(values) do fn(i,{get=function() return v end}) end end
    function a:Empty() values={} end
    return setmetatable(a,{
        __index=function(_,i) if type(i)=='number' then return values[i] end end,
        __newindex=function(_,i,v) assert(type(i)=='number' and i>=1 and i<=#values+1);values[i]=v end,
    })
end
function effect(id,parameter)
    local e=obj({name='Effect_'..tostring({}),class=classes['mucha.CPP_ContFxEncountRatio']})
    function e:GetEffectData() return {ID=id,EffectType=192,ParamList=array({id==71000 and 0 or 50})} end
    function e:GetTargetUnitParameter() return parameter end
    return e
end
function parameter(name)
    return obj({name=name,class=classes['mucha.CPP_UnitParameter'],m_ContEffectList=array({})})
end
parameters={[1001]=parameter('Rain_Parameter'),[1002]=parameter('Lasswell_Parameter')}
function has_effect(p,id)
    local found=false
    p.m_ContEffectList:ForEach(function(_,v) if v:get():GetEffectData().ID==id then found=true end end)
    return found
end
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
function map:GetMapUnitParameter(id) assert(id>=1001 and id<=1008);return parameters[id] end
local units=obj({})
function units:GetPlayableUnitParameterObj(id) return parameters[id] end
local skills=obj({})
function skills:GetSkillEffectDataById(id)
    assert(id==nativeSource.effect.ID)
    return {ID=id,EffectType=badNativeEffect and 0 or nativeSource.enums['eSkillEffectType.EncountRatio'],
        ParamList=array({nativeSource.effect.ParamList[1]})}
end
function skills:CreateContEffect(source,target,data,skillId,passive,schedule)
    assert(source==target and data.ID==71000 and data.EffectType==192 and data.ParamList[1]==0)
    assert(skillId==nativeSource.passive.ID and passive==true and schedule==false)
    effectCreations=(effectCreations or 0)+1
    local e=effect(71000,target)
    if factoryAttaches then local a=target.m_ContEffectList;a[a:GetArrayNum()+1]=e end
    return e
end
local signatures={
 ['mucha.CPP_BFL_Map:GetMapUnitParameter']={'IntProperty','ObjectProperty'},
 ['mucha.CPP_BFL_Unit:GetPlayableUnitParameterObj']={'IntProperty','ObjectProperty'},
 ['mucha.CPP_BFL_Skill:GetSkillEffectDataById']={'IntProperty','StructProperty'},
 ['mucha.CPP_BFL_Skill:CreateContEffect']={'ObjectProperty','ObjectProperty','StructProperty','IntProperty','BoolProperty','BoolProperty','ObjectProperty'},
}
local talk=obj({})
function talk:IsPlayingEvent() return event end
local libs={['mucha.Default__CPP_BFL_Map']=map,['mucha.Default__CPP_BFL_TalkEvent']=talk,
    ['Engine.Default__SubsystemBlueprintLibrary']=systems,['Engine.Default__GameplayStatics']=gameplay,
    ['mucha.Default__CPP_BFL_Skill']=skills,['mucha.Default__CPP_BFL_Unit']=units}
function StaticFindObject(p)
    if p:find('/Script/',1,true)~=1 then return nil end
    local n=p:gsub('^/Script/','')
    return libs[n] or classes[n] or obj({ForEachProperty=function(_,fn)
        for _,kind in ipairs(signatures[n] or {}) do fn({GetFullName=function() return kind..' '..n end}) end
    end})
end
local factory=obj()
local guideClass=obj({name='WBP_StudioStatus_C'})
libs['UMG.Default__WidgetBlueprintLibrary']=factory
function LoadAsset(path)
    assert(path=='/Game/UI/Studio/WBP_StudioStatus.WBP_StudioStatus_C')
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
        function p:GetVisibility() return self.visibility end
        function p:SetRenderOpacity(value) self.opacity=value end
        function p:GetRenderOpacity() return self.opacity end
        return p
    end
    local label=part()
    function label:SetText(s)
        assert(type(s)=='table' and s.nativeType=='FText','Native FText input required')
        self.label=s.value
    end
    function label:GetText() return FText(self.label or '') end
    local t=part();t.Text_Name=label;t.WBP_DirectionGridPanel=obj();t.Horizontal_Content=part()
    function t.WBP_DirectionGridPanel:SetVisibility(v) assert(v==1) end
    function t.WBP_DirectionGridPanel:GetVisibility() return 1 end
    function t:AddToViewport(z)
        assert(z==50);viewport[#viewport+1]=self
        -- Native Construct happens here, after Create returns.
        self.visibility=1;self.Horizontal_Content.visibility=1;label.visibility=1
        self.opacity=0;self.Horizontal_Content.opacity=0;label.opacity=0
    end
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
function FText(value) assert(type(value)=='string');return {nativeType='FText',value=value,ToString=function(self) return self.value end} end
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
    local rain,lasswell=parameters[1001],parameters[1002]
    local foreign=effect(12000,rain);rain.m_ContEffectList[1]=foreign
    event=true;tick();assert(created==0 and #viewport==0)
    event=false;tick();assert(actor.m_OverwriteEncountRatio==-1 and #panel.children==1 and #viewport==1)
    assert(lastText.label:find('ON') and lastWidget.position.Y==-24)
    for _,part in ipairs({lastWidget,lastText}) do
        assert(part.visibility==3 and part.opacity==1,'Reveal guide content after native Construct')
    end
    press();assert(has_effect(rain,71000) and has_effect(lasswell,71000) and lastText.label:find('OFF'))
    assert(actor.m_OverwriteEncountRatio==-1 and actor.m_EncountThresholdDistance==1200)
    local creations=effectCreations
    collectgarbage('collect');tick();assert(effectCreations==creations,'Do not duplicate owned effects')
    -- Native input/guide updates may hide the content again; re-show our own widgets.
    lastText.visibility=1;lastText.label='native reset';tick()
    assert(lastText.visibility==3 and lastText.label:find('OFF'))
    press();assert(not has_effect(rain,71000) and not has_effect(lasswell,71000))
    assert(rain.m_ContEffectList:GetArrayNum()==1 and rain.m_ContEffectList[1]==foreign)
    -- Do not remove an equipped/natively present Dragon Seal effect.
    local equipped=effect(71000,rain);rain.m_ContEffectList[2]=equipped
    press();assert(rain.m_ContEffectList[2]==equipped)
    press();assert(rain.m_ContEffectList[2]==equipped and rain.m_ContEffectList:GetArrayNum()==2)
    rain.m_ContEffectList:Empty();rain.m_ContEffectList[1]=foreign
    -- Factories that attach immediately must not cause double insertion.
    factoryAttaches=true;press();assert(rain.m_ContEffectList:GetArrayNum()==2)
    press();assert(rain.m_ContEffectList:GetArrayNum()==1);factoryAttaches=false
    -- Hold both triggers for a full second, latched until released.
    controller.left,controller.right=1,1;tick(.1);tick(.9)
    assert(not FFRStudioEncounterToggle.disabled)
    tick(.11);assert(FFRStudioEncounterToggle.disabled and has_effect(rain,71000))
    tick(3);assert(FFRStudioEncounterToggle.disabled)
    controller.left=0;tick();controller.left=1;tick();tick(1.1)
    assert(not FFRStudioEncounterToggle.disabled and not has_effect(rain,71000))
    controller.left,controller.right=0,0;tick()
    -- Menus, events, transitions and fights release only owned effects.
    press();local oldText=lastWidget
    for _,flag in ipairs({'event','menuOpen','inBattle'}) do
        _G[flag]=true;press();assert(not has_effect(rain,71000) and oldText.removed)
        assert(FFRStudioEncounterToggle.disabled and rain.m_ContEffectList[1]==foreign)
        _G[flag]=false;tick();assert(has_effect(rain,71000));oldText=lastWidget
    end
    local h=hooks['/Script/mucha.CPP_MapManager:Encount'];h[1]();h[2]()
    assert(not has_effect(rain,71000) and FFRStudioEncounterToggle.disabled)
    -- A new native map parameter cache never keeps the old owned effects.
    local old=rain;parameters[1001]=parameter('Rain_NewMap');rain=parameters[1001]
    actor=new_actor('Rain_B',.75);hud,panel=new_hud();tick()
    assert(not has_effect(old,71000) and has_effect(rain,71000) and old.m_ContEffectList[1]==foreign)
    assert(#panel.children==1 and #viewport==1 and lastText.label:find('OFF'))
    -- Native parameter rebuilds while still walking are refreshed before InputMove.
    rain.m_ContEffectList:Empty();hooks['/Script/mucha.CPP_MapUnit_Playable:InputMove'][1]()
    assert(has_effect(rain,71000))
    press();assert(not has_effect(rain,71000) and actor.m_OverwriteEncountRatio==.75)
    -- Missing HUD refuses hidden toggles; failed creation cleans up its viewport entry.
    local good=controller;controller=nil;press();assert(not has_effect(rain,71000))
    assert(not FFRStudioEncounterToggle.disabled);controller=good;tick()
    event=true;tick();event=false;failPosition=true;tick();assert(#viewport==0)
    failPosition=false;tick();assert(#viewport==1 and lastText.label:find('ON'))
    -- Unsupported native effect data fails without changing any actor/party state.
    badNativeEffect=true;press();assert(not has_effect(rain,71000) and not has_effect(lasswell,71000))
    assert(actor.m_OverwriteEncountRatio==.75 and actor.m_EncountThresholdDistance==1200)
    badNativeEffect=false;tick();assert(has_effect(rain,71000));press()
    -- Weak callback registries still see the rooted late game-thread callback.
    local weak=setmetatable({}, {__mode='v'})
    ExecuteInGameThread=function(fn) weak.callback=fn end
    for i=1,45 do FFRStudioEncounterToggle.async() end
    collectgarbage('collect');assert(type(weak.callback)=='function');weak.callback()
end
