-- Repeat native UI selections. Never submit fabricated battle jobs, change
-- costs/save data, or carry enemy unique IDs into another battle.
local config=require('config')
if config.autoBattle~=1 then return end
local runtime={enabled=false,memory={},hooks={},injecting=false}
-- Captured native player attacks. Dark Fina's party ID precedes Jake/Sakura,
-- so this is not an arithmetic conversion from UnitId.
local attacks={[1001]=401010,[1002]=402010,[1003]=403010,[1004]=404010,
    [1005]=405010,[1006]=408010,[1007]=406010,[1008]=407010}
_G.FFRStudioAutoBattle=runtime -- Native callback registries can hold weak references.
local display,painted,replay,lastTurn,holdStart,held,lastError,battleKey
local function valid(o)
    return o~=nil and (type(o)=='table' or type(o)=='userdata') and o:IsValid()
end
local function native(n)
    local o=StaticFindObject('/Script/'..n)
    assert(valid(o),'Native auto-battle object unavailable: '..n)
    return o
end
local function each(a,fn)
    if not a then return end
    local count=0
    local function visit(v)
        count=count+1;assert(count<=128,'Unexpected native command array size')
        if (type(v)=='table' or type(v)=='userdata') and type(v.get)=='function' then v=v:get() end
        fn(v)
    end
    if type(a)=='table' and type(a.ForEach)~='function' then
        for _,v in ipairs(a) do visit(v) end
    else a:ForEach(function(_,v) visit(v) end) end
end
local function list(a) local r={};each(a,function(v) r[#r+1]=v end);return r end
local function key(k) return {Category=k.Category,ID=k.ID} end
local function instance(class,predicate)
    local result
    for _,o in ipairs(FindAllOf(class) or {}) do
        if valid(o) and not o:GetFullName():find('Default__',1,true) and predicate(o) then
            assert(not result,'Ambiguous native '..class);result=o
        end
    end
    return result
end
-- These read-only helpers were not in the initial survey. Verify their
-- reflected argument/return kinds before calling; no guessed offsets/defaults.
local checked={}
local function signature(name,kinds)
    if checked[name] then return end
    local fields={}
    native('mucha.'..name):ForEachProperty(function(p)
        fields[#fields+1]=p:GetFullName():match('^(%w+)')
    end)
    assert(table.concat(fields,',')==kinds,'Unsupported native signature: '..name)
    checked[name]=true
end
local function unit_id(id)
    signature('CPP_BFL_Battle:GetUnitIdByUniqueId','IntProperty,IntProperty')
    return native('mucha.Default__CPP_BFL_Battle'):GetUnitIdByUniqueId(id)
end
local function relation(id)
    signature('CPP_BFL_Battle:GetBattleUnitParameter','IntProperty,ObjectProperty')
    local p=native('mucha.Default__CPP_BFL_Battle'):GetBattleUnitParameter(id)
    assert(valid(p),'Target parameter unavailable')
    return p:GetRelation()
end
local function clear_display()
    if display then display:remove() end
    display,painted=nil,nil
end
local function suspend()
    replay,lastTurn,holdStart=nil,nil,nil
    -- A held chord stays latched through transient input/command transitions.
    -- It must be released before it may enable auto-battle again.
    clear_display()
end
local function pause(reason)
    local changed=runtime.enabled or runtime.reason~=tostring(reason):gsub('[\r\n]',' '):sub(1,64)
    runtime.enabled=false;replay=nil
    runtime.reason=tostring(reason):gsub('[\r\n]',' '):sub(1,64)
    if changed then print('[FFR auto battle] Paused: '..reason..'\n') end
end
local function command_phase(phase)
    -- Native eBtlPhaseType / eBtlCmdType: Normal=0, Additional=1, Finish=2.
    return phase==0 or phase==1
end
local function context()
    local ui=instance('CPP_UI_BattleSubsystem',function(o) return o.bDuringBattle end)
    if not ui or not command_phase(ui.BtlPhaseType) then return end
    if native('Engine.Default__GameplayStatics'):IsGamePaused(ui) then return end
    local input=native('Engine.Default__SubsystemBlueprintLibrary'):GetWorldSubsystem(ui,native('mucha.CPP_InputManager'))
    if not valid(input) or not input:IsEnableInput() then return end
    local view=instance('CPP_VM_Battle',function(o) return o.bIsDisplayBattleWidget end)
    if not view or view.bIsEvent or not view.bIsSequenceUIVisible then return end
    local vm=instance('CPP_VM_BtlCmd',function(o) return o.bDisplayCmd end)
    -- The guide/toggle also works during ordinary enemy turns.
    return {ui=ui,view=view,vm=vm,manager=ui.BtlCmdManager}
end
local function position_guide(c)
    -- Follow the real speed widget in viewport coordinates, without reparenting
    -- anything in the game's HUD. Fallback is used until its first layout pass.
    local ok=pcall(function()
        local speed=instance('WBP_BtlKeyGuide_Speed_C',function(o)
            local player=native('Engine.Default__GameplayStatics'):GetPlayerController(o,0)
            return o:IsVisible() and valid(player) and player:GetFullName()==display.controller:GetFullName()
        end)
        if not speed then return end
        local slate=native('UMG.Default__SlateBlueprintLibrary')
        local geometry=speed:GetCachedGeometry();local size=slate:GetLocalSize(geometry)
        if size.X<=0 or size.Y<=0 then return end
        local viewport=native('UMG.Default__WidgetLayoutLibrary'):GetViewportWidgetGeometry(c.ui)
        local extent=slate:GetLocalSize(viewport)
        local absolute=slate:LocalToAbsolute(geometry,{X=0,Y=0})
        local p=slate:AbsoluteToLocal(viewport,absolute)
        -- A visible child can belong to an inactive/hidden guide. Never move
        -- the bottom indicator to a stale title/menu widget's top geometry.
        if p.Y<extent.Y*.5 or p.Y+size.Y>extent.Y then return end
        local x=p.X>454 and p.X-442 or p.X+size.X+12
        x=math.max(16,math.min(x,extent.X-446))
        local previous=display.footerPosition
        if previous and math.abs(previous.X-x)<.5 and math.abs(previous.Y-p.Y)<.5 then return end
        display.widget:SetAnchorsInViewport({Minimum={X=0,Y=0},Maximum={X=0,Y=0}})
        display.widget:SetAlignmentInViewport({X=0,Y=0})
        display.widget:SetPositionInViewport({X=x,Y=p.Y},false)
        display.footerPosition={X=x,Y=p.Y}
    end)
    return ok
end
local function guide(c)
    if display and (not display:valid() or display.context:GetFullName()~=c.ui:GetFullName()) then clear_display() end
    if not display then
        display=create_status_hud(c.ui,{anchorX=1,anchorY=1,x=-24,y=-64,width=430})
        if not display then return false end
    end
    local label='▶ Auto: '..(runtime.enabled and 'ON' or 'OFF')..'   F9 / Hold LT+RT (L2+R2)'
    if runtime.reason then label=label..' — '..runtime.reason end
    if painted~=label then display:set(label);painted=label end
    display:show()
    position_guide(c)
    return true
end
local function current_unit(c)
    if not valid(c.manager) or not command_phase(c.manager.CmdType) or not c.vm then return end
    local ids=list(c.manager.ActionUnitUniqueIdList)
    if #ids==0 then return end
    signature('CPP_UI_BtlCmdManager:GetCurrentActionUnitUniqueId','IntProperty')
    local id=c.manager:GetCurrentActionUnitUniqueId()
    local found=false
    for _,candidate in ipairs(ids) do if candidate==id then found=true;break end end
    if not found then return end
    local stable=unit_id(id)
    if stable<1001 or stable>1008 then return end
    return id,stable
end
local function saved(stable,vm)
    local save=instance('CPP_MuchaGameSaveData',function() return true end)
    if not save then return end
    local memory
    each(save.unitParameterList,function(p)
        if p.UnitId~=stable then return end
        local bundle=p.btlCmdData;local actions={}
        each(bundle.cmdDataList,function(a)
            actions[#actions+1]={id=a.actionId,item=a.isUseItem,all=false,friendly={},params=list(a.ParameterList)}
        end)
        if #actions==0 then return end
        local path={}
        if bundle.CommandId>0 and bundle.CommandId~=actions[1].id then path[#path+1]={Category=1,ID=bundle.CommandId} end
        if #path==0 and not actions[1].item then
            signature('CPP_BFL_Skill:GetSkillDataById','IntProperty,StructProperty')
            local data=native('mucha.Default__CPP_BFL_Skill'):GetSkillDataById(actions[1].id)
            each(data.belongCommandList,function(parent)
                local k={Category=1,ID=parent}
                if #path==0 and vm:CanActivateAction(k) then path[#path+1]=k end
            end)
        end
        for _,a in ipairs(actions) do path[#path+1]={Category=a.item and 2 or 1,ID=a.id} end
        memory={path=path,actions=actions}
    end)
    return memory
end
local function resolved_path(memory,vm)
    if #memory.path>0 then return memory.path end
    local first=memory.actions[1];local path={}
    if memory.command and memory.command>0 and memory.command~=first.id then
        path[1]={Category=1,ID=memory.command}
    elseif not first.item and first.id~=0 then
        signature('CPP_BFL_Skill:GetSkillDataById','IntProperty,StructProperty')
        local data=native('mucha.Default__CPP_BFL_Skill'):GetSkillDataById(first.id)
        each(data.belongCommandList,function(parent)
            local k={Category=1,ID=parent}
            if #path==0 and vm:CanActivateAction(k) then path[1]=k end
        end)
    end
    for _,a in ipairs(memory.actions) do path[#path+1]={Category=a.item and 2 or 1,ID=a.id} end
    return path
end
local function remember(owner,wrapped)
    local ok,message=pcall(function()
        -- DecideCommand can run after native input/the command widget closes.
        -- Capture the native decision independently of the interactive UI guard.
        local manager=owner:get()
        if not valid(manager) then return end
        -- The native submission can close the UI or advance its phase before
        -- this hook. Those transient flags must never discard a newer command.
        local ui=instance('CPP_UI_BattleSubsystem',function(o)
            return valid(o.BtlCmdManager) and o.BtlCmdManager:GetFullName()==manager:GetFullName()
        end)
        if not ui then return end
        local data=wrapped:get();local actions={};local stable
        each(data.DecideDataList,function(a)
            local owner=unit_id(a.actionUnitUniqueId)
            if owner<1001 or owner>1008 then return end
            assert(not stable or stable==owner,'Mixed command actors')
            stable=owner;local friends={}
            each(a.targetUnitUniqueIdList,function(id)
                local target=unit_id(id)
                if target>=1001 and target<=1008 then friends[#friends+1]=target end
            end)
            actions[#actions+1]={id=a.actionId,item=a.isUseItem,all=a.IsAll,friendly=friends,params=list(a.ParameterList)}
        end)
        if not stable or #actions==0 then return end
        if replay and replay.stable==stable and replay.submitting then
            replay.committed=true;return -- Keep the original target preferences.
        end
        local path={}
        pcall(function() each(data.SelectedActionPathList,function(k) path[#path+1]=key(k) end) end)
        -- A completed/cleared native stack may be absent or contain old history.
        -- Keep the new actions anyway and rebuild their hierarchy when needed.
        local matches=#path>=#actions
        for i,a in ipairs(actions) do
            local k=path[#path-#actions+i]
            if not k or k.ID~=a.id or k.Category~=(a.item and 2 or 1) then matches=false end
        end
        if not matches then path={} end
        runtime.sequence=(runtime.sequence or 0)+1
        runtime.memory[stable]={path=path,actions=actions,command=data.CommandId,sequence=runtime.sequence}
        local ids={};for _,a in ipairs(actions) do ids[#ids+1]=tostring(a.id) end
        print('[FFR auto battle] Remembered unit='..stable..'; actions='..table.concat(ids,',')..
            '; sequence='..runtime.sequence..'; path='..#path..'; phase='..tostring(ui.BtlPhaseType)..'\n')
    end)
    if not ok then print('[FFR auto battle] Memory unavailable: '..tostring(message)..'\n') end
end
local function inject(command,fn)
    -- A native query can dispatch input callbacks before it returns. Recheck
    -- immediately before each write, rather than trusting advance's old state.
    if not runtime.enabled or replay~=command then return false end
    runtime.injecting=true;local ok,error=pcall(fn);runtime.injecting=false
    if not ok then error= tostring(error);pause(error) end
    return ok
end
local function advance(c,now)
    local id,stable=current_unit(c)
    if not id then replay,lastTurn=nil,nil;return end
    if not replay then
        -- Turning on midway through manual input leaves that command to the player.
        if c.manager.CmdState~=0 or #list(c.vm.CommandStack)~=0 or lastTurn==c.manager:GetFullName()..':'..id then return end
        local memory=runtime.memory[stable] or saved(stable,c.vm)
        if not memory then
            local attack=attacks[stable]
            memory={path={{Category=1,ID=attack}},actions={{id=attack,item=false,all=false,friendly={},params={}}},fallback=true}
            runtime.memory[stable]=memory
            print('[FFR auto battle] No command memory; using native Attack for unit='..stable..'\n')
        end
        -- Resolve on the current actor's live menu. Never reuse a stale command
        -- merely because the newer submission lacked its selected-path array.
        memory.path=resolved_path(memory,c.vm)
        if not runtime.enabled then replay=nil;return end
        local ids={};for _,a in ipairs(memory.actions) do ids[#ids+1]=tostring(a.id) end
        print('[FFR auto battle] Replaying unit='..stable..'; actions='..table.concat(ids,',')..
            '; memory='..tostring(memory.sequence or (memory.fallback and 'Attack fallback' or 'native saved'))..'\n')
        replay={stable=stable,id=id,manager=c.manager:GetFullName(),memory=memory,index=1,target=1,at=now}
    end
    local r=replay
    if r.manager~=c.manager:GetFullName() or r.id~=id or r.committed then
        lastTurn=r.manager..':'..r.id;replay=nil;return
    end
    if now-r.at>5 then pause('Command did not advance');return end
    if c.manager.CmdState==0 then
        local k=r.memory.path[r.index]
        if not k then
            if r.target<=#r.memory.actions then pause('Command path incomplete');return end
            r.submitting=true
            inject(r,function() c.vm:EndCommand() end)
            lastTurn=r.manager..':'..id;replay=nil;return
        end
        -- GetCommands() returns FBtlCmdStackData (already selected commands),
        -- not menu entries. Native CanActivateAction is the availability check.
        if not c.vm:CanActivateAction(k) then
            print('[FFR auto battle] Unavailable unit='..stable..'; step='..r.index..'; action='..k.Category..':'..k.ID..'\n')
            pause('Remembered action unavailable');return
        end
        r.index=r.index+1;r.at=now
        inject(r,function() c.vm:DecideActionKey(k) end)
    elseif c.manager.CmdState==1 then
        local selector=c.vm.UnitSelectVM
        if not valid(selector) then return end
        local value=selector:GetCmdValue();local a=r.memory.actions[r.target]
        if not a or value.ActionKey.ID~=a.id or value.ActionKey.Category~=(a.item and 2 or 1) then pause('Target action changed');return end
        if table.concat(list(value.ParamList),',')~=table.concat(a.params or {},',') then pause('Command parameters changed');return end
        local targets=list(selector:GetTargetUniqueIdList());local all=value.IsAll or (a.all and selector.bCanBeAoE)
        if a.all and selector.bCanBeAoE then
            local wanted=#a.friendly>0 and 1 or (#targets>0 and relation(targets[1]) or 0)
            targets={}
            each(selector.targetUniqueIdList,function(candidate)
                if relation(candidate)==wanted then targets[#targets+1]=candidate end
            end)
        end
        if #targets==0 then pause('No legal target');return end
        if not all and #a.friendly>0 then
            local legal=list(selector.targetUniqueIdList)
            local found=false
            for _,wanted in ipairs(a.friendly) do
                for _,candidate in ipairs(legal) do
                    if unit_id(candidate)==wanted then targets={candidate};found=true;break end
                end
            end
            if not found then
                targets={}
                for _,candidate in ipairs(legal) do
                    if relation(candidate)==1 then targets={candidate};break end
                end
                if #targets==0 then pause('No legal friendly target');return end
            end
        end
        r.target=r.target+1;r.at=now;r.submitting=r.target>#r.memory.actions and r.index>#r.memory.path
        inject(r,function() c.vm:DecideTarget(targets,all) end)
        if r.committed then lastTurn=r.manager..':'..id;replay=nil end
    end
end
local function toggle()
    runtime.enabled=not runtime.enabled;runtime.reason=nil;replay=nil;lastTurn=nil
    print('[FFR auto battle] '..(runtime.enabled and 'ON' or 'OFF')..'\n')
end
local function update(press)
    -- OFF is a Lua-only cancellation and must work even while the command UI
    -- temporarily disables input. Never leave replay armed behind that guard.
    local switchedOff=press and runtime.enabled
    if switchedOff then toggle();press=false;held=true end
    local c=context()
    if not c then suspend();return end
    local newBattle=c.ui:GetFullName()..':'..c.ui.BtlPhaseType
    if battleKey~=newBattle then replay,lastTurn=nil,nil;battleKey=newBattle end
    if not guide(c) then pause('Battle guide unavailable');return end
    local gameplay=native('Engine.Default__GameplayStatics')
    local now=gameplay:GetRealTimeSeconds(c.ui)
    local controller=display.controller
    local left=controller:GetInputAnalogKeyState({KeyName=FName('Gamepad_LeftTriggerAxis')})
    local right=controller:GetInputAnalogKeyState({KeyName=FName('Gamepad_RightTriggerAxis')})
    if left>=.8 and right>=.8 then
        if not holdStart or now<holdStart then holdStart=now end
        if not held and now-holdStart>=1 then held=true;toggle() end
    else holdStart,held=nil,false end
    if press then toggle() end
    if runtime.enabled then advance(c,now) end
    guide(c)
end
local function guarded(press)
    local ok,error=pcall(update,press)
    if not ok then
        pcall(function() pause(tostring(error));clear_display() end)
        if lastError~=tostring(error) then print('[FFR auto battle] '..tostring(error)..'\n') end
        lastError=tostring(error)
    else lastError=nil end
    return false
end
runtime.tick=function() return guarded(false) end
runtime.key_action=function() guarded(true) end
runtime.key=function() ExecuteInGameThread(runtime.key_action) end
RegisterKeyBind(Key.F9,runtime.key)
runtime.remember=remember;runtime.remember_post=function() end
RegisterHook('/Script/mucha.CPP_UI_BtlCmdManager:DecideCommand',runtime.remember,runtime.remember_post)
runtime.manual=function()
    if not runtime.injecting and replay then pause('Manual control') end
end
runtime.manual_post=function() end
RegisterHook('/Script/mucha.CPP_VM_BtlCmd:DecideActionKey',runtime.manual,runtime.manual_post)
RegisterHook('/Script/mucha.CPP_VM_BtlCmd:DecideTarget',runtime.manual,runtime.manual_post)
runtime.begin=function() replay,lastTurn=nil,nil end
RegisterHook('/Script/mucha.CPP_UI_BtlCmdManager:HandleBeginCommand',runtime.manual_post,runtime.begin)
local loop=false
if type(LoopInGameThreadWithDelay)=='function' then loop=pcall(LoopInGameThreadWithDelay,100,runtime.tick) end
if not loop then
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
print('[FFR auto battle] Ready: F9 or hold LT+RT/L2+R2 for one second. Starts OFF.\n')
