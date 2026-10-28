-- Read-only, F8-only battle command survey. No hooks, timers, command execution,
-- native offsets, asset loads, save writes, input injection or option changes.
local runtime={pending=false,bookmarks=0,lines=0}
_G.FFRStudioBattleCommandObserver=runtime
local function emit(kind,fields)
    if runtime.lines>=2500 then return end
    runtime.lines=runtime.lines+1
    print('[FFR Battle Commands] '..kind..' | '..table.concat(fields or {},' | ')..'\n')
end
local function read(label,fn)
    local ok,value=pcall(fn)
    if ok then return value end
    emit('UNAVAILABLE',{label,tostring(value):gsub('[\r\n|]',' '):sub(1,200)})
end
local function valid(o)
    return o~=nil and (type(o)=='table' or type(o)=='userdata') and o:IsValid()
end
local function name(o) return valid(o) and o:GetFullName() or '-' end
local function scalar(v)
    if v==nil then return '?' end
    if type(v)=='number' or type(v)=='boolean' or type(v)=='string' then return tostring(v) end
    return v:ToString()
end
local function each(array,fn)
    if not array then return end
    local count=0
    array:ForEach(function(_,wrapped)
        count=count+1
        if count<=128 then fn(wrapped:get(),count) end
    end)
end
local function numbers(array)
    local result={};each(array,function(v) result[#result+1]=scalar(v) end)
    return table.concat(result,',')
end
local function instances(class,fn)
    local found=read('find:'..class,function() return FindAllOf(class) end) or {}
    for i,o in ipairs(found) do
        if i<=64 and valid(o) and not name(o):find('Default__',1,true) then
            read(class,function() fn(o) end)
        end
    end
end
local methods={
    'CPP_BtlInput:OnAutoBattle','CPP_BtlAutoCmdManager:OnPushCommand',
    'CPP_OptionFunctionHandler:HandleAutoBattle','CPP_BFL_Battle:IsAutoBattle',
    'CPP_BFL_Battle:IsEnableCommand','CPP_BFL_Battle:CanUnitActivateSkill',
    'CPP_UI_BtlCmdManager:DecideCommand','CPP_UI_BtlCmdManager:HandleBeginCommand',
    'CPP_UI_BtlCmdManager:AbortCommand','CPP_VM_BtlCmd:OpenCommand',
    'CPP_VM_BtlCmd:DecideActionKey','CPP_VM_BtlCmd:CanActivateAction',
    'CPP_VM_BtlCmd:DecideTarget','CPP_VM_BtlCmd:EndCommand',
    'CPP_VM_BtlCmdUnitSelect:DecideCmd','CPP_VM_BtlCmdUnitSelect:SetCmdValue',
    'CPP_VM_BtlCmdUnitSelect:GetCmdValue','CPP_VM_BtlCmdUnitSelect:GetTargetUniqueIdList',
    'CPP_BFL_SaveDataOption:GetOptionSetting','CPP_BFL_SaveDataOption:GetSaveOptionRadioButtonValue',
    'CPP_BFL_SaveDataOption:GetSaveOptionValue','CPP_VM_Battle:IsAutoBattle',
    'CPP_BtlDelEventCmd:OnExecuteDecideCommand','CPP_BtlDelEventCmd:OnExecuteAutoCommand',
    'CPP_BtlUnitParameter:GetMimicCmdValue','CPP_KeyGuideSubsystem:FindKeyGuideData',
    'CPP_UI_BattleSubsystem:HandleBeginBtl','CPP_UI_BattleSubsystem:HandleEndBtl',
}
local function signatures()
    for _,method in ipairs(methods) do
        read('signature:'..method,function()
            local fn=StaticFindObject('/Script/mucha.'..method)
            if not valid(fn) then emit('FUNCTION_MISSING',{method});return end
            local fields={method}
            fn:ForEachProperty(function(property) fields[#fields+1]=property:GetFullName() end)
            emit('SIGNATURE',fields)
        end)
    end
end
local function action(key) return scalar(key.Category)..':'..scalar(key.ID) end
local function command(value,label)
    emit(label,{'action='..action(value.ActionKey),'targets='..numbers(value.TargetIdList),
        'parameters='..numbers(value.ParamList),'all='..scalar(value.IsAll)})
end
local function saved(o)
    each(o.unitParameterList,function(p)
        -- Party members only; IDs identify the actor across different battles.
        if p.UnitId<1001 or p.UnitId>1008 then return end
        local b=p.btlCmdData
        emit('SAVED_COMMAND',{'unit='..p.UnitId,'command='..scalar(b.CommandId)})
        each(b.cmdDataList,function(cmd)
            emit('SAVED_ACTION',{'unit='..p.UnitId,'action='..scalar(cmd.actionId),
                'item='..scalar(cmd.isUseItem),'targets='..numbers(cmd.targetUnitUniqueIdList),
                'parameters='..numbers(cmd.ParameterList)})
        end)
    end)
end
local function widget(o,depth,seen)
    if depth>7 or runtime.widgetCount>=180 or not valid(o) then return end
    local key=name(o)
    if seen[key] then return end
    seen[key]=true;runtime.widgetCount=runtime.widgetCount+1
    local fields={'depth='..depth,key,'visibility='..scalar(o:GetVisibility())}
    read('widget slot',function()
        local slot=o.Slot
        fields[#fields+1]='slot='..name(slot)
        if valid(slot) and slot:IsA(StaticFindObject('/Script/UMG.CanvasPanelSlot')) then
            local p=slot:GetPosition();local size=slot:GetSize();local a=slot:GetAnchors()
            fields[#fields+1]=string.format('position=%.1f,%.1f;size=%.1f,%.1f;anchors=%.2f,%.2f/%.2f,%.2f',
                p.X,p.Y,size.X,size.Y,a.Minimum.X,a.Minimum.Y,a.Maximum.X,a.Maximum.Y)
        end
    end)
    emit('WIDGET',fields)
    if o:IsA(StaticFindObject('/Script/UMG.UserWidget')) then
        if valid(o.WidgetTree) then widget(o.WidgetTree.RootWidget,depth+1,seen) end
    elseif o:IsA(StaticFindObject('/Script/UMG.PanelWidget')) then
        local count=o:GetChildrenCount()
        if count>=0 and count<128 then
            for i=0,count-1 do widget(o:GetChildAt(i),depth+1,seen) end
        end
    end
end
local function snapshot()
    runtime.bookmarks=runtime.bookmarks+1
    emit('BOOKMARK',{'number='..runtime.bookmarks})
    signatures()
    instances('CPP_MuchaGameSaveData',saved)
    instances('CPP_MuchaOptionSaveData',function(o)
        local count=0
        o.EnvironmentData:ForEach(function(key,value)
            count=count+1
            if count<=128 then
                emit('GAME_OPTION',{'tag='..scalar(key:get().TagName),'value='..numbers(value:get().Value)})
            end
        end)
    end)
    instances('CPP_BtlManager',function(o)
        emit('BATTLE_MANAGER',{name(o),'input='..name(o.m_pBtlInput),'autoManager='..name(o.m_pAutoCmdManager)})
    end)
    instances('CPP_VM_Battle',function(o)
        emit('BATTLE_VIEW',{name(o),'auto='..scalar(o:IsAutoBattle()),
            'display='..scalar(o.bIsDisplayBattleWidget),'event='..scalar(o.bIsEvent),
            'sequenceUI='..scalar(o.bIsSequenceUIVisible)})
    end)
    instances('CPP_UI_BattleSubsystem',function(o)
        emit('BATTLE_UI',{name(o),'during='..scalar(o.bDuringBattle),
            'phase='..scalar(o.BtlPhaseType),'actionUnit='..scalar(o.CurrentActionUnitUniqueId),
            'commandManager='..name(o.BtlCmdManager)})
    end)
    instances('CPP_UI_BtlCmdManager',function(o)
        emit('COMMAND_MANAGER',{name(o),'type='..scalar(o.CmdType),'state='..scalar(o.CmdState),
            'unitIndex='..scalar(o.ActionUnitIndex),'units='..numbers(o.ActionUnitUniqueIdList),
            'specificUnit='..scalar(o.SpecificActionUnitUniqueId)})
    end)
    instances('CPP_VM_BtlCmd',function(o)
        emit('COMMAND_VIEW',{name(o),'display='..scalar(o.bDisplayCmd),'stack='..name(o.CmdStack),
            'unitSelect='..name(o.UnitSelectVM)})
        each(o.CommandStack,function(c,i)
            emit('STACK',{'index='..i,'state='..scalar(c.BtlCmdState),'action='..action(c.ActionKey),
                'all='..scalar(c.IsAll),'parameters='..numbers(c.ParamList)})
        end)
    end)
    instances('CPP_VM_BtlCmdUnitSelect',function(o)
        emit('TARGET_VIEW',{name(o),'targetIds='..numbers(o.targetUniqueIdList),
            'focus='..scalar(o.FocusBaseUniqueId),'canAoE='..scalar(o.bCanBeAoE)})
        command(o.CmdValue,'CURRENT_ACTION')
    end)
    instances('CPP_WBP_TagKeyGuideList',function(o)
        emit('KEY_GUIDES',{name(o),'visibility='..scalar(o:GetVisibility())})
        each(o.KeyGuideTagList,function(t) emit('KEY_GUIDE_TAG',{scalar(t.TagName)}) end)
    end)
    runtime.widgetCount=0
    instances('WBP_BattleLayout_C',function(o) widget(o,0,{}) end)
    emit('BOOKMARK_END',{'number='..runtime.bookmarks,'widgets='..runtime.widgetCount})
end
-- Keep the same closures alive for native weak callback registries.
runtime.queued=function()
    runtime.pending=false
    if runtime.bookmarks>=8 then return end
    read('snapshot',snapshot)
end
runtime.key=function()
    if runtime.pending or runtime.bookmarks>=8 then return end
    runtime.pending=true
    local ok,message=pcall(ExecuteInGameThread,runtime.queued)
    if not ok then runtime.pending=false;emit('QUEUE_UNAVAILABLE',{tostring(message)}) end
end
RegisterKeyBind(Key.F8,runtime.key)
emit('READY',{'F8 snapshots only; maximum 8; no timers or gameplay changes'})
