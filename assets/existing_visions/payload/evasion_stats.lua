-- Read the selected native parameter's current effects. No stat/save mutation,
-- actor lookup, equipment prediction, retained UObjects or raw memory. A bounded
-- game-thread UI observer waits for native entries without hiding valid values.
local config = require('config')
if config.evasionStats ~= 1 then return end
local runtime = {hooks={}, callbacks={}, busy=false, errors={}, layouts={}, targets={}}
_G.FFRStudioEvasionStats = runtime
local widgetClass = '/Game/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitParam_Detail.WBP_UnitParam_Detail_C'
local checked = {}
local function unwrap(o)
    if (type(o)=='userdata' or type(o)=='table') and type(o.get)=='function' then return o:get() end
    return o
end
local function live(o)
    return o~=nil and (type(o)=='userdata' or type(o)=='table') and o:IsValid()
        and not o:HasAnyFlags(0x40018000)
end
local function native(name)
    local o=StaticFindObject('/Script/'..name)
    assert(live(o),'Native evasion object unavailable: '..name)
    return o
end
local function signature(path, expected)
    if checked[path] then return end
    local fn=StaticFindObject(path)
    assert(live(fn),'Missing evasion function: '..path)
    local types={}
    fn:ForEachProperty(function(p) types[#types+1]=p:GetFullName():match('^(%w+)') end)
    local actual=table.concat(types,',')
    assert(actual==expected or (type(expected)=='table' and expected[actual]),'Unsupported evasion signature: '..path)
    checked[path]=true
end
local function list(array)
    local values={}
    assert(array~=nil,'Native effect array unavailable')
    if type(array)=='table' and type(array.ForEach)~='function' then
        for _,v in ipairs(array) do values[#values+1]=unwrap(v) end
    else array:ForEach(function(_,v) values[#values+1]=unwrap(v) end) end
    return values
end
local function integer(value)
    assert(type(value)=='number' and value==math.floor(value) and value>=-2147483648
        and value<=2147483647,'Unsupported native evasion value')
    return value
end
local function float32(value)
    local rounded=string.unpack('<f',string.pack('<f',value))
    return rounded
end
local function cap(context)
    signature('/Script/mucha.CPP_InputManager:GetDataTable',{
        ['EnumProperty,ObjectProperty']=true,['ByteProperty,ObjectProperty']=true})
    local systems=native('Engine.Default__SubsystemBlueprintLibrary')
    local input=systems:GetWorldSubsystem(context,native('mucha.CPP_InputManager'))
    assert(live(input),'Native calculation table manager unavailable')
    local source=input:GetDataTable(19) -- eDataTableType.UnitParameterCalc, same live table as native hit calculation.
    assert(live(source) and source:IsA(native('Engine.DataTable')),'Native calculation table unavailable')
    local schema=source:GetRowStruct()
    assert(live(schema) and schema:GetFullName()=='ScriptStruct /Script/mucha.UNIT_PARAMETER_CALC_DATA',
        'Unsupported native calculation table schema')
    local row=source:FindRow('ダメージ計算用パラメータ')
    -- A FindRow value is struct memory, not a UObject. Never read UObject
    -- flags from that pointer (even for a purported safety check).
    assert(row~=nil and type(row.type)=='function' and row:type()=='UScriptStruct' and row:IsValid(),
        'Native calculation row unavailable')
    return integer(row.evasionLimit)
end
local function selected(widget)
    local vm=widget.CPP_VM_UnitParam
    if not live(vm) then return end
    local parameter
    if vm:IsA(native('mucha.CPP_VM_BtlUnitParam')) then
        parameter=vm.BtlUnitParam -- Never fall back to a menu snapshot in battle.
        if not live(parameter) or not parameter:IsA(native('mucha.CPP_BtlUnitParameter')) then return end
    else parameter=vm.UnitParam end
    if not live(parameter) or not parameter:IsA(native('mucha.CPP_UnitParameter')) then return end
    signature('/Script/mucha.CPP_UnitParameter:GetRelation',{['ByteProperty']=true,['EnumProperty']=true})
    if parameter:GetRelation()~=1 then return end -- Party characters only; reveal no enemy stats.
    return parameter
end
local function current(parameter, limit)
    signature('/Script/mucha.CPP_UnitParameter:GetContEffectList','ArrayProperty')
    signature('/Script/mucha.CPP_ContEffect:GetEffectData','StructProperty')
    local physical,magical,decoy=0,0,false
    for _,effect in ipairs(list(parameter:GetContEffectList())) do
        if live(effect) then
            if effect:IsA(native('mucha.CPP_ContFxAvoidance')) then
                -- Verified native getter 0x05111a90: selector byte 0 applies to
                -- both types, 1 physical, 2 magic; missing values default to -1.
                -- Lifetime/activation are managed by the game's active list.
                local data=effect:GetEffectData()
                local p=list(data.ParamList)
                local kind=integer(p[2] or -1)%256
                local amount=integer(p[1] or -1)
                if kind==0 or kind==1 then physical=float32(physical+float32(amount)) end
                if kind==0 or kind==2 then magical=float32(magical+float32(amount)) end
            elseif effect:IsA(native('mucha.CPP_ContFxDecoy')) then
                -- Native +0x4b0 override 0x0514ed70 forces physical avoidance
                -- before the ordinary cap/accuracy roll. No magic override.
                decoy=true
            end
        end
    end
    -- The native getter returns integer contributions; the hit routine sums
    -- them then applies min(live evasionLimit,sum). Raw 500 is capped too.
    -- This is the evasion component, not a prediction for an incoming attack.
    local function capped(value)
        value=math.min(float32(limit),value)
        return integer(value<0 and math.ceil(value) or math.floor(value))
    end
    return decoy and 100 or capped(physical),capped(magical)
end
local function named(object,name)
    return live(object) and object:GetFullName():match('[%.:]([^%.:]+)$')==name
end
local function labels(widget)
    -- Keep the shared Blueprint's original six fields. Existing parent pages
    -- serialize child instances against that exact unversioned schema. Added
    -- text is game-owned WidgetTree content, not new reflected BP properties.
    local tree=widget.WidgetTree
    if not live(tree) then return end
    local root=tree.RootWidget
    if not named(root,'VerticalBox_StudioStats') or not root:IsA(native('UMG.PanelWidget')) then return end
    signature('/Script/UMG.PanelWidget:GetChildrenCount','IntProperty')
    signature('/Script/UMG.PanelWidget:GetChildAt','IntProperty,ObjectProperty')
    if root:GetChildrenCount()~=2 then return end
    local overlay,reserve=root:GetChildAt(0),root:GetChildAt(1)
    if not named(overlay,'Overlay_0') or not overlay:IsA(native('UMG.PanelWidget')) or
        overlay:GetChildrenCount()~=3 or not named(reserve,'Spacer_StudioEvasionRoom') then return end
    local result={reserve=reserve,overlay=overlay}
    for i,kind in ipairs({'Physical','Magical'}) do
        local row=overlay:GetChildAt(i) -- Child 0 remains the native grid wrapper.
        if not named(row,'HorizontalBox_Studio'..kind..'Evasion') or
            not row:IsA(native('UMG.PanelWidget')) or row:GetChildrenCount()~=3 then return end
        local icon,label,number=row:GetChildAt(0),row:GetChildAt(1),row:GetChildAt(2)
        if not named(icon,'Image_Studio'..kind..'Evasion') or not icon:IsA(native('UMG.Image')) then return end
        if not named(label,'Text_Studio'..kind..'Evasion') or
            not named(number,'Text_Studio'..kind..'EvasionValue') then return end
        local textClass=native('CommonUI.CommonTextBlock')
        if not label:IsA(textClass) or not number:IsA(textClass) then return end
        result[kind]={label,number,icon}
        result[kind].row=row
    end
    return result
end
local function entries(widget)
    local wrapper=widget.WBP_DirectionGridPanel
    if not live(wrapper) then return end
    local panel=wrapper.GridPanel_28 -- The captured Blueprint's visible native grid.
    if not live(panel) or not panel:IsA(native('UMG.GridPanel')) then return end
    local count=panel:GetChildrenCount()
    assert(count>=0 and count<=128,'Unsupported stat-grid entry count')
    local result={}
    local entryType=StaticFindObject('/Game/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitParam_DetailEntry.WBP_UnitParam_DetailEntry_C')
    assert(live(entryType),'Native stat entry class is unavailable')
    for i=0,count-1 do
        local entry=panel:GetChildAt(i)
        if live(entry) and entry:IsA(entryType) and live(entry.Slot) and entry.Slot:IsA(native('UMG.GridSlot')) then
            result[#result+1]=entry
        end
    end
    table.sort(result,function(a,b)
        return a.Slot.Row<b.Slot.Row or (a.Slot.Row==b.Slot.Row and a.Slot.Column<b.Slot.Column)
    end)
    return result,panel,wrapper
end
local function position(row,top)
    local slot=row.Slot
    assert(live(slot) and slot:IsA(native('UMG.OverlaySlot')),'Evasion overlay slot is unavailable')
    slot:SetPadding({Left=0,Top=top,Right=0,Bottom=0})
end
local function set_slot(slot,name,value)
    if name=='Row' then slot:SetRow(value)
    elseif name=='RowSpan' then slot:SetRowSpan(value)
    elseif name=='Column' then slot:SetColumn(value)
    else slot:SetColumnSpan(value) end
end
local function clear_layout(widget,rows)
    local cache=runtime.layouts[tostring(widget:GetAddress())]
    local _,panel=entries(widget)
    local nodes={}
    if live(panel) then
        for i=0,panel:GetChildrenCount()-1 do
            local node=panel:GetChildAt(i);if live(node) then nodes[#nodes+1]=node end
        end
    end
    if cache then for _,node in ipairs(nodes) do
        local slot=node.Slot
        if live(slot) then
            for name,value in pairs(cache.slots[tostring(slot:GetAddress())] or {}) do
                -- A native rebuild may already have reset a slot. Restore only
                -- values we still own, preserving newly generated native data.
                if slot[name]==value.applied then set_slot(slot,name,value.original) end
            end
        end
        local size=cache.spacers[tostring(node:GetAddress())]
        if size and node.Size.X==size.x and node.Size.Y==size.applied then node:SetSize({X=size.x,Y=size.y}) end
    end
        cache.slots={};cache.spacers={};cache.stamp=nil
    end
    rows.reserve:SetSize({X=0,Y=0})
    for _,kind in ipairs({'Physical','Magical'}) do position(rows[kind].row,0) end
end
local function finite(n) return type(n)=='number' and n==n and math.abs(n)<1e6 end
local function fallback(widget,rows,children,panel,wrapper)
    -- The native grid is top aligned in the cooked asset, so extra Overlay
    -- height cannot centre it down into these temporary below-grid rows.
    clear_layout(widget,rows)
    widget:ForceLayoutPrepass()
    local height=children[1]:GetDesiredSize().Y
    if not finite(height) or height<=0 then height=32 end
    local profile=wrapper.DirGridPanelProperty
    local gap=profile.GridDirection==0 and profile.SpaceBetweenEntryInGridDirection or profile.SpaceBetweenLine
    if not finite(gap) or gap<0 or gap>100 then gap=0 end
    local total=panel:GetDesiredSize().Y
    assert(finite(total) and total>=0,'Native stat panel extent is unavailable')
    local top=wrapper.Slot.Padding.Top+total+gap
    position(rows.Physical.row,top+(height-rows.Physical.row:GetDesiredSize().Y)/2)
    position(rows.Magical.row,top+height+gap+(height-rows.Magical.row:GetDesiredSize().Y)/2)
end
local function layout_stamp(widget,rows)
    local children,panel,wrapper=entries(widget)
    assert(children and live(panel),'Native stat entries are not ready')
    local types={};for _,entry in ipairs(children) do types[tostring(entry:GetAddress())]=entry.UnitParamType end
    local parts={tostring(wrapper:GetAddress()),wrapper.Slot.Padding.Top,wrapper.DirGridPanelProperty.GridDirection,
        #list(wrapper.EntryList),tostring(rows.Physical.row:GetAddress()),tostring(rows.Magical.row:GetAddress()),
        rows.Physical.row:GetDesiredSize().Y,rows.Magical.row:GetDesiredSize().Y}
    for i=0,panel:GetChildrenCount()-1 do
        local node=panel:GetChildAt(i);local slot=node.Slot
        if live(node) and live(slot) then
            parts[#parts+1]=table.concat({tostring(node:GetAddress()),types[tostring(node:GetAddress())] or -1,node:GetDesiredSize().Y,
                slot.Row,slot.RowSpan,slot.Column,slot.ColumnSpan,slot.Padding.Top,slot.Padding.Bottom,
                node:IsA(native('UMG.Spacer')) and node.Size.Y or -1},':')
        end
    end
    return table.concat(parts,'|')
end
local function reflow(widget,rows)
    signature('/Script/UMG.Widget:ForceLayoutPrepass','')
    signature('/Script/UMG.Widget:GetDesiredSize','StructProperty')
    signature('/Script/UMG.OverlaySlot:SetPadding','StructProperty')
    signature('/Script/UMG.Spacer:SetSize','StructProperty')
    for _,name in ipairs({'SetRow','SetRowSpan','SetColumn','SetColumnSpan'}) do
        signature('/Script/UMG.GridSlot:'..name,'IntProperty')
    end
    local key=tostring(widget:GetAddress())
    local cache=runtime.layouts[key]
    if not cache then cache={slots={},spacers={},attempts=0};runtime.layouts[key]=cache end
    if cache.stamp and not cache.pending then
        widget:ForceLayoutPrepass()
        if cache.stamp==layout_stamp(widget,rows) then return end
    end
    clear_layout(widget,rows)
    widget:ForceLayoutPrepass()
    local children,panel,wrapper=entries(widget)
    assert(children and #children>0,'Native stat entries are not ready')
    cache.pending=false
    for _,entry in ipairs(children) do
        if entry.Slot.Column~=children[1].Slot.Column or wrapper.DirGridPanelProperty.GridDirection~=0 then
            fallback(widget,rows,children,panel,wrapper);return -- Preserve native comparison grids.
        end
    end
    local spacers={}
    for _,record in ipairs(list(wrapper.EntryList)) do
        if live(record) and live(record.Widget) and live(record.Spacer) then
            spacers[tostring(record.Widget:GetAddress())]=record.Spacer
        end
    end
    local plan={};local top=wrapper.Slot.Padding.Top;local found={}
    for i,entry in ipairs(children) do
        local slot=entry.Slot;local size=entry:GetDesiredSize();local padding=slot.Padding
        assert(finite(size.Y) and size.Y>0,'Native stat desired size is not ready')
        local height=size.Y+padding.Top+padding.Bottom
        local spacer=spacers[tostring(entry:GetAddress())]
        local gap=0
        if i<#children then
            assert(live(spacer) and live(spacer.Slot) and spacer.Slot:IsA(native('UMG.GridSlot')),
                'Native stat spacer is not ready')
            gap=spacer:GetDesiredSize().Y+spacer.Slot.Padding.Top+spacer.Slot.Padding.Bottom
            assert(finite(gap) and gap>=0 and gap<200,'Native stat gap is unavailable')
        end
        local kind=entry.UnitParamType==13 and 'Physical' or entry.UnitParamType==15 and 'Magical'
        local extra=0
        if kind then
            assert(i<#children and spacer.Visibility~=1,'Native defence spacer is unavailable')
            extra=height+gap
            found[kind]=top+height+gap+padding.Top+(size.Y-rows[kind].row:GetDesiredSize().Y)/2
        end
        plan[#plan+1]={entry=entry,spacer=spacer,row=2*(i-1),extra=extra}
        top=top+height+gap+extra
    end
    assert(found.Physical and found.Magical,'Native defence rows are unavailable')
    local function set(slot,name,value)
        local id=tostring(slot:GetAddress());cache.slots[id]=cache.slots[id] or {}
        cache.slots[id][name]={original=slot[name],applied=value};set_slot(slot,name,value)
    end
    for _,record in ipairs(plan) do
        local entry,spacer=record.entry,record.spacer
        -- One native row per entry and one per spacer makes desired-height
        -- layout deterministic even when the original grid uses spanning cells.
        set(entry.Slot,'Row',record.row);set(entry.Slot,'RowSpan',1)
        if live(spacer) then
            set(spacer.Slot,'Row',record.row+1);set(spacer.Slot,'RowSpan',1)
            set(spacer.Slot,'Column',entry.Slot.Column);set(spacer.Slot,'ColumnSpan',entry.Slot.ColumnSpan)
            if record.extra>0 then
                local x,y=spacer.Size.X,spacer.Size.Y
                cache.spacers[tostring(spacer:GetAddress())]={x=x,y=y,applied=y+record.extra}
                spacer:SetSize({X=x,Y=y+record.extra})
            end
        end
    end
    for kind,value in pairs(found) do position(rows[kind].row,value) end
    widget:ForceLayoutPrepass()
    cache.stamp=layout_stamp(widget,rows)
end
local function hide(widget)
    local rows=labels(widget)
    if rows then for _,kind in ipairs({'Physical','Magical'}) do
        local pair=rows[kind]
        for _,child in ipairs(pair) do if live(child) then child:SetVisibility(1) end end
    end
        pcall(clear_layout,widget,rows)
    end
    runtime.layouts[tostring(widget:GetAddress())]=nil
end
local function refresh(context)
    if runtime.busy then return end
    local widget=unwrap(context)
    if not live(widget) or not live(widget:GetClass()) or
        widget:GetClass():GetFullName()~='WidgetBlueprintGeneratedClass '..widgetClass then return end
    local path=widget:GetFullName():match('^%S+ (.+)$')
    if path then
        runtime.targets[path]=tostring(widget:GetAddress())
        local count=0;for _ in pairs(runtime.targets) do count=count+1 end
        if count>4 then
            runtime.busy=true
            for oldPath,oldKey in pairs(runtime.targets) do
                local oldWidget=StaticFindObject(oldPath)
                if live(oldWidget) and tostring(oldWidget:GetAddress())==oldKey then
                    local oldRows=labels(oldWidget)
                    if oldRows then pcall(clear_layout,oldWidget,oldRows) end
                end
            end
            runtime.busy=false
            runtime.targets={[path]=tostring(widget:GetAddress())};runtime.layouts={}
        end
    end
    runtime.busy=true
    local ok,err=pcall(function()
        local parameter=selected(widget)
        if not parameter then hide(widget); return end
        local physical,magical=current(parameter,cap(widget))
        local values={Physical=physical,Magical=magical}
        local rows=labels(widget)
        assert(rows,'Evasion stat rows are missing; rebuild/install the mod')
        for kind,short in pairs({Physical='Phys. Eva.',Magical='Mag. Eva.'}) do
            local label,number=rows[kind][1],rows[kind][2]
            label:SetText(FText(short))
            number:SetText(FText(tostring(values[kind])..'%'))
            for _,child in ipairs(rows[kind]) do
                child:SetToolTipText(FText('Equipped loadout and active effects on this page. Equipment comparisons show equipped values. Attack accuracy and guaranteed-hit rules can change the result.'))
                child:SetVisibility(3)
            end
        end
        local positioned,message=pcall(reflow,widget,rows)
        if not positioned then
            local key=tostring(widget:GetAddress())
            local cache=runtime.layouts[key] or {slots={},spacers={},attempts=0}
            runtime.layouts[key]=cache;cache.pending=cache.attempts<5
            local available,children,panel,wrapper=pcall(entries,widget)
            if available and children and #children>0 then pcall(fallback,widget,rows,children,panel,wrapper) end
            message='Layout fallback: '..tostring(message)
            if not runtime.errors[message] then runtime.errors[message]=true;print('[FFR evasion] '..message..'\n') end
        end
    end)
    if not ok then
        pcall(hide,widget) -- Never leave stale/partial figures after a failed read.
        local message=tostring(err)
        if not runtime.errors[message] then runtime.errors[message]=true; print('[FFR evasion] '..message..'\n') end
    end
    runtime.busy=false
end
runtime.rebuild=function(context)
    local widget=unwrap(context)
    if live(widget) then
        local cache=runtime.layouts[tostring(widget:GetAddress())]
        if cache then cache.attempts=0;cache.stamp=nil end
    end
    refresh(context)
end
runtime.tick=function()
    for path,key in pairs(runtime.targets) do
        local cache=runtime.layouts[key]
        if cache and cache.pending then
            local widget=StaticFindObject(path)
            if live(widget) and tostring(widget:GetAddress())==key then
                cache.attempts=cache.attempts+1
                runtime.measuring=true
                local ok,message=pcall(refresh,widget)
                runtime.measuring=false
                if not ok then print('[FFR evasion] Layout retry: '..tostring(message)..'\n') end
            else runtime.targets[path]=nil;runtime.layouts[key]=nil end
        end
    end
    return false
end
local function attach()
    local added=false
    for _,name in ipairs({'CreateList','HandleUnitParamUpdate','SetCPP_VM_UnitParam','SetUnitParamVM','SetUnitId','SetItemId'}) do
        local path=widgetClass..':'..name
        local fn=StaticFindObject(path)
        if live(fn) and runtime.hooks[path]~=fn:GetAddress() then
            local ok=pcall(function()
                RegisterHook(path,name=='CreateList' and runtime.rebuild or refresh) -- Post-Blueprint callback.
                runtime.hooks[path]=fn:GetAddress()
                added=true
            end)
            if not ok then print('[FFR evasion] Stat update hook unavailable: '..name..'\n') end
        end
    end
    if added then
        -- Class-load notifications precede the next game-thread callback. The
        -- first page may already have initialized; refresh those instances once.
        local widgets=FindAllOf('WBP_UnitParam_Detail_C')
        if widgets then for _,widget in ipairs(list(widgets)) do refresh(widget) end end
    end
end
runtime.refresh,runtime.attach=refresh,attach
runtime.queued=function() runtime.pending=false;attach() end
runtime.discover=function()
    if runtime.pending then return end
    runtime.pending=true
    ExecuteInGameThread(runtime.queued)
end
runtime.callbacks={refresh,attach,runtime.discover,runtime.queued,runtime.rebuild,runtime.tick}
-- Observe class loading rather than every actor/widget instance. No borrowed
-- object pointer is carried into the game-thread attachment callback.
NotifyOnNewObject('/Script/UMG.WidgetBlueprintGeneratedClass',runtime.discover)
ExecuteInGameThread(attach)
local observer=false
if type(LoopInGameThreadWithDelay)=='function' then observer=pcall(LoopInGameThreadWithDelay,100,runtime.tick) end
if not observer and type(LoopAsync)=='function' then
    runtime.uiQueued=function() runtime.uiPending=false;runtime.tick() end
    runtime.uiAsync=function()
        if not runtime.uiPending then
            runtime.uiPending=true
            if not pcall(ExecuteInGameThread,runtime.uiQueued) then runtime.uiPending=false end
        end
        return false
    end
    observer=pcall(LoopAsync,100,runtime.uiAsync)
end
if not observer then print('[FFR evasion] UI observer unavailable\n') end
print('[FFR evasion] Current physical/magical stat rows ready\n')
