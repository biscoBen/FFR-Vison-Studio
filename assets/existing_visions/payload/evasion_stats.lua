-- Read the selected native parameter's current effects. No stat/save mutation,
-- actor lookup, equipment prediction, timers, retained UObjects or raw memory.
local config = require('config')
if config.evasionStats ~= 1 then return end
local runtime = {hooks={}, callbacks={}, busy=false, errors={}}
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
    if root:GetChildrenCount()~=3 then return end
    local result={}
    for i,kind in ipairs({'Physical','Magical'}) do
        local row=root:GetChildAt(i) -- Child 0 is the untouched native stat grid.
        if not named(row,'HorizontalBox_Studio'..kind..'Evasion') or
            not row:IsA(native('UMG.PanelWidget')) or row:GetChildrenCount()~=2 then return end
        local label,number=row:GetChildAt(0),row:GetChildAt(1)
        if not named(label,'Text_Studio'..kind..'Evasion') or
            not named(number,'Text_Studio'..kind..'EvasionValue') then return end
        local textClass=native('CommonUI.CommonTextBlock')
        if not label:IsA(textClass) or not number:IsA(textClass) then return end
        result[kind]={label,number}
    end
    return result
end
local function hide(widget)
    local rows=labels(widget)
    if rows then for _,pair in pairs(rows) do
        for _,child in ipairs(pair) do if live(child) then child:SetVisibility(1) end end
    end end
end
local function refresh(context)
    if runtime.busy then return end
    local widget=unwrap(context)
    if not live(widget) or not live(widget:GetClass()) or
        widget:GetClass():GetFullName()~='WidgetBlueprintGeneratedClass '..widgetClass then return end
    runtime.busy=true
    local ok,err=pcall(function()
        local parameter=selected(widget)
        if not parameter then hide(widget); return end
        local physical,magical=current(parameter,cap(widget))
        local values={Physical=physical,Magical=magical}
        local rows=labels(widget)
        assert(rows,'Evasion stat rows are missing; rebuild/install the mod')
        for kind,short in pairs({Physical='Phys. Eva',Magical='Mag. Eva'}) do
            local label,number=rows[kind][1],rows[kind][2]
            label:SetText(FText(short))
            number:SetText(FText(tostring(values[kind])..'%'))
            for _,child in ipairs({label,number}) do
                child:SetToolTipText(FText('Equipped loadout and active effects on this page. Equipment comparisons show equipped values. Attack accuracy and guaranteed-hit rules can change the result.'))
                child:SetVisibility(3)
            end
        end
    end)
    if not ok then
        pcall(hide,widget) -- Never leave stale/partial figures after a failed read.
        local message=tostring(err)
        if not runtime.errors[message] then runtime.errors[message]=true; print('[FFR evasion] '..message..'\n') end
    end
    runtime.busy=false
end
local function attach()
    local added=false
    for _,name in ipairs({'CreateList','HandleUnitParamUpdate','SetCPP_VM_UnitParam','SetUnitParamVM','SetUnitId','SetItemId'}) do
        local path=widgetClass..':'..name
        local fn=StaticFindObject(path)
        if live(fn) and runtime.hooks[path]~=fn:GetAddress() then
            local ok=pcall(function()
                RegisterHook(path,refresh) -- Blueprint callback runs after the original body.
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
runtime.callbacks={refresh,attach,runtime.discover,runtime.queued}
-- Observe class loading rather than every actor/widget instance. No borrowed
-- object pointer is carried into the game-thread attachment callback.
NotifyOnNewObject('/Script/UMG.WidgetBlueprintGeneratedClass',runtime.discover)
ExecuteInGameThread(attach)
print('[FFR evasion] Current physical/magical stat rows ready\n')
