-- Native UI protocol fixture, using the user's 344 -> 420070 target snapshot.
clock=0;active=false;paused=false;inputEnabled=true;event=false;phase=0
keys={};hooks={};logs={};submissions={};availableMP=10;requiredActions=1;guideAvailable=true
local function object(name,fields)
    fields=fields or {};fields.name=name
    function fields:IsValid() return true end
    function fields:GetFullName() return self.name end
    return fields
end
function wrapped(v) return {get=function() return v end} end
function array(v)
    return {ForEach=function(_,fn) for i,value in ipairs(v) do fn(i,wrapped(value)) end end}
end
actionId=420070;actionCategory=1;parentId=344;itemQty=2
local function akey(id) return {Category=id==actionId and actionCategory or 1,ID=id} end
actor=1;enemy=8;friend=4
controller=object('Controller',{left=0,right=0})
function controller:GetInputAnalogKeyState(k) return k.KeyName=='Gamepad_LeftTriggerAxis' and self.left or self.right end
local gameplay=object('Gameplay')
function gameplay:GetRealTimeSeconds() return clock end
function gameplay:IsGamePaused() return paused end
function gameplay:GetPlayerController() return controller end
local input=object('Input',{IsEnableInput=function() return inputEnabled end})
local systems=object('Systems',{GetWorldSubsystem=function() return input end})
local battle=object('Battle')
function battle:GetUnitIdByUniqueId(id)
    if id==actor then return 1001 elseif id==friend then return 1002 else return 40040 end
end
function battle:GetBattleUnitParameter(id)
    return object('Parameter', {GetRelation=function() return (id==actor or id==friend) and 1 or 2 end})
end
local skills=object('Skills',{GetSkillDataById=function(_,id) assert(id==420070);return {belongCommandList=array({344})} end})
local signatures={
 ['CPP_BFL_Battle:GetUnitIdByUniqueId']={'IntProperty','IntProperty'},
 ['CPP_BFL_Battle:GetBattleUnitParameter']={'IntProperty','ObjectProperty'},
 ['CPP_VM_BtlCmd:GetCommands']={'ArrayProperty'},
 ['CPP_BFL_Skill:GetSkillDataById']={'IntProperty','StructProperty'},
}
function StaticFindObject(path)
    local n=path:gsub('^/Script/','')
    if n=='Engine.Default__GameplayStatics' then return gameplay end
    if n=='Engine.Default__SubsystemBlueprintLibrary' then return systems end
    if n=='mucha.Default__CPP_BFL_Battle' then return battle end
    if n=='UMG.Default__WidgetLayoutLibrary' then return object('Viewport',{
        GetViewportWidgetGeometry=function() return {size={X=1920,Y=1080}} end}) end
    if n=='UMG.Default__SlateBlueprintLibrary' then return object('Slate',{
        GetLocalSize=function(_,g) return g.size end,
        LocalToAbsolute=function(_,g,p) return g.position end,
        AbsoluteToLocal=function(_,g,p) return p end}) end
    if n=='mucha.Default__CPP_BFL_Skill' then return skills end
    local fn=n:gsub('^mucha%.','')
    return object(n,{ForEachProperty=function(_,visit)
        for _,kind in ipairs(signatures[fn] or {}) do visit({GetFullName=function() return kind..' /Script/'..n end}) end
    end})
end
function FName(n) return n end
Key={F9=120}
function print(s) logs[#logs+1]=s end
function RegisterKeyBind(k,fn) keys[k]=fn end
function RegisterHook(p,pre,post) hooks[p]={pre,post} end
function ExecuteInGameThread(fn) fn() end
function LoopAsync(ms,fn) async=fn end
save=object('Save',{unitParameterList=array({{UnitId=1001,btlCmdData={CommandId=-1,
    cmdDataList=array({{actionId=420070,isUseItem=false,ParameterList=array({})}})}}})})
view=object('View',{bIsDisplayBattleWidget=true,bIsEvent=false,bIsSequenceUIVisible=true})
manager=object('Manager',{CmdType=0,CmdState=0,ActionUnitUniqueIdList=array({actor})})
ui=object('BattleWorld',{bDuringBattle=true,BtlPhaseType=0,BtlCmdManager=manager})
selector=object('Selector',{bCanBeAoE=true,FocusBaseUniqueId=enemy})
vm=object('CommandView',{bDisplayCmd=true,CommandStack=array({}),UnitSelectVM=selector})
stack={};pendingActions={};selectedPath={};reserved=0
local function present(list,id) for _,v in ipairs(list) do if v==id then return true end end end
function vm:GetCommands()
    return array(stack) -- Native return: selected FBtlCmdStackData, not menu entries.
end
function vm:CanActivateAction(k)
    if menuChanged then return false end
    return (k.ID==parentId and #stack==0) or
        (k.ID==actionId and #stack>0 and ((actionCategory==2 and itemQty-reserved>=1) or
        (actionCategory~=2 and availableMP-reserved>=1)))
end
function vm:DecideActionKey(k)
    hooks['/Script/mucha.CPP_VM_BtlCmd:DecideActionKey'][1](wrapped(self),wrapped(k))
    assert(self.bDisplayCmd and self:CanActivateAction(k),'Illegal/costly command')
    assert(k.ID==(#stack==0 and parentId or actionId),'Command not in the native current menu')
    stack[#stack+1]={ActionKey=akey(k.ID)};self.CommandStack=array(stack)
    selectedPath[#selectedPath+1]=akey(k.ID)
    if k.ID==actionId then
        manager.CmdState=1
        selector.CmdValue={ActionKey=akey(k.ID),IsAll=false,ParamList=array({})}
        selector.targetUniqueIdList=array({enemy,enemy+1,friend})
    end
end
function selector:GetCmdValue() return self.CmdValue end
function selector:GetTargetUniqueIdList() return array({enemy}) end
function vm:DecideTarget(ids,all)
    hooks['/Script/mucha.CPP_VM_BtlCmd:DecideTarget'][1](wrapped(self),wrapped(ids),wrapped(all))
    assert(manager.CmdState==1 and #ids>0)
    for _,id in ipairs(ids) do assert(present({enemy,enemy+1,friend},id),'Stale/illegal target') end
    pendingActions[#pendingActions+1]={actionId=actionId,actionUnitUniqueId=actor,isUseItem=actionCategory==2,
        IsAll=all,targetUnitUniqueIdList=array(ids),ParameterList=array({})}
    reserved=reserved+1;manager.CmdState=0
    if #pendingActions>=requiredActions then self:EndCommand() end
end
function vm:EndCommand()
    assert(#pendingActions==requiredActions,'Do not submit a partial multicast')
    assert((actionCategory==2 and itemQty or availableMP)>=reserved,'Do not bypass MP checks')
    local data={DecideDataList=array(pendingActions),SelectedActionPathList=array(selectedPath)}
    hooks['/Script/mucha.CPP_UI_BtlCmdManager:DecideCommand'][1](wrapped(manager),wrapped(data))
    submissions[#submissions+1]=data
    if actionCategory==2 then itemQty=itemQty-reserved else availableMP=availableMP-reserved end
    self.bDisplayCmd=false;manager.ActionUnitUniqueIdList=array({})
end
function FindAllOf(class)
    if class=='CPP_MuchaGameSaveData' then return {save} end
    if not active then return {} end
    if class=='CPP_UI_BattleSubsystem' then ui.BtlPhaseType=phase;return {ui} end
    if class=='CPP_VM_Battle' then view.bIsEvent=event;return {view} end
    if class=='CPP_VM_BtlCmd' then return {vm} end
    if class=='WBP_BtlKeyGuide_Speed_C' and showSpeed then
        return {object('SpeedGuide',{IsVisible=function() return true end,
            GetOwningPlayer=function() return controller end,
            GetCachedGeometry=function() return {position={X=1000,Y=30},size={X=100,Y=40}} end})}
    end
    return {}
end
function create_status_hud(context,position)
    assert(active and context==ui and not paused and inputEnabled,'Never create UI on title/pause')
    if not guideAvailable then return end
    guidesCreated=(guidesCreated or 0)+1
    local d={context=ui,controller=controller,widget=object('OwnedGuide')}
    function d.widget:SetAnchorsInViewport(a) end
    function d.widget:SetAlignmentInViewport(a) end
    function d.widget:SetPositionInViewport(p,dpi) guidePosition=p end
    guidePosition={X=position.x,Y=position.y,anchorY=position.anchorY}
    function d:valid() return not self.removed end
    function d:set(s) badge=s end
    function d:remove() self.removed=true;guidesRemoved=(guidesRemoved or 0)+1 end
    return d
end
package.preload.config=function() return {autoBattle=1} end
function tick(dt) clock=clock+(dt or .1);FFRStudioAutoBattle.tick() end
function press() keys[Key.F9]() end
function new_turn()
    stack={};selectedPath={};pendingActions={};reserved=0
    vm.bDisplayCmd=true;vm.CommandStack=array({});manager.CmdState=0
    manager.ActionUnitUniqueIdList=array({actor})
    hooks['/Script/mucha.CPP_UI_BtlCmdManager:HandleBeginCommand'][2]()
end
function manual(path,all,friendlyTarget)
    local actions={}
    for i=1,requiredActions do actions[i]={actionId=actionId,actionUnitUniqueId=actor,isUseItem=actionCategory==2,
        IsAll=all or false,ParameterList=array({}),targetUnitUniqueIdList=array({friendlyTarget or enemy})} end
    local keys={};for _,id in ipairs(path or {344,420070}) do keys[#keys+1]=akey(id) end
    hooks['/Script/mucha.CPP_UI_BtlCmdManager:DecideCommand'][1](wrapped(manager),wrapped({
        DecideDataList=array(actions),SelectedActionPathList=array(keys)}))
end
