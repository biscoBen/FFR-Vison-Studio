-- Reflection, out-struct and lifecycle boundaries model the pinned UE4SS API.
config={evasionStats=1}; package.preload.config=function() return config end
hooks,queue,logs={}, {}, {}; loaded=false; gameThread=false
function print(message) logs[#logs+1]=message end
function param(value) return {get=function() return value end} end
function object(name)
    local o={name=name, flags=0}
    function o:IsValid() return not self.dead end
    function o:HasAnyFlags(flags) return self.flags & flags ~= 0 end
    function o:GetFullName() return self.name end
    function o:GetAddress() return self.name end
    function o:IsA(cls) return cls.name==self.class or (self.parents and self.parents[cls.name]) or false end
    return o
end
cls='/Game/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitParam_Detail.WBP_UnitParam_Detail_C'
functions={
 ['/Script/mucha.CPP_InputManager:GetDataTable']={'EnumProperty','ObjectProperty'},
 ['/Script/mucha.CPP_UnitParameter:GetRelation']={'ByteProperty'},
 ['/Script/mucha.CPP_UnitParameter:GetContEffectList']={'ArrayProperty'},
 ['/Script/mucha.CPP_ContEffect:GetEffectData']={'StructProperty'},
 ['/Script/UMG.PanelWidget:GetChildrenCount']={'IntProperty'},
 ['/Script/UMG.PanelWidget:GetChildAt']={'IntProperty','ObjectProperty'},
}
natives={}
function StaticFindObject(path)
    if path:sub(1,#cls)==cls and not loaded then return object('unloaded').missing end
    local o=natives[path]
    if not o then
        o=object(path);natives[path]=o
        function o:ForEachProperty(fn)
            for _,p in ipairs(functions[path] or {}) do fn(object(p..' property')) end
        end
    end
    return o
end
function RegisterHook(path,callback)
    assert(gameThread and not hooks[path]);hooks[path]=callback
end
function ExecuteInGameThread(callback) queue[#queue+1]=callback end
function NotifyOnNewObject(path,callback)
    assert(path=='/Script/UMG.WidgetBlueprintGeneratedClass');discover=callback
end
function FindAllOf(name) assert(name=='WBP_UnitParam_Detail_C');return {param(widget)} end
function drain()
    gameThread=true
    while #queue>0 do table.remove(queue,1)() end
    gameThread=false
end
function FText(value) return {text=value} end
function label(name)
    local o=object('CommonTextBlock /Fixture.WidgetTree.'..name)
    o.class='/Script/CommonUI.CommonTextBlock'
    function o:SetText(text) assert(gameThread and type(text)=='table');self.value=text.text end
    function o:SetToolTipText(text) assert(gameThread and type(text)=='table');self.tooltip=text.text end
    function o:SetVisibility(value) assert(gameThread);self.visibility=value end
    return o
end
widget=object('Stat page');widgetType=object('WidgetBlueprintGeneratedClass '..cls)
function widget:GetClass() return widgetType end
physicalLabel=label('Text_StudioPhysicalEvasion');magicalLabel=label('Text_StudioMagicalEvasion')
physicalValue=label('Text_StudioPhysicalEvasionValue');magicalValue=label('Text_StudioMagicalEvasionValue')
physicalIcon=label('Image_StudioPhysicalEvasion');magicalIcon=label('Image_StudioMagicalEvasion')
physicalIcon.class='/Script/UMG.Image';magicalIcon.class='/Script/UMG.Image'
function panel(name,children)
    local p=object('PanelWidget /Fixture.WidgetTree.'..name)
    p.class='/Script/UMG.PanelWidget';p.children=children
    function p:GetChildrenCount() assert(gameThread);return #self.children end
    function p:GetChildAt(index) assert(gameThread);return self.children[index+1] end
    return p
end
root=panel('VerticalBox_StudioStats',{
    object('Untouched native grid'),
    panel('HorizontalBox_StudioPhysicalEvasion',{physicalIcon,physicalLabel,physicalValue}),
    panel('HorizontalBox_StudioMagicalEvasion',{magicalIcon,magicalLabel,magicalValue})})
widget.WidgetTree=object('WidgetTree');widget.WidgetTree.RootWidget=root
setmetatable(widget,{__index=function(_,key)
    if key:match('^Text_Studio') then error('Shared widget has no added reflected fields') end
end})
function parameter(isBattle)
    local p=object('Parameter')
    p.class='/Script/mucha.CPP_'..(isBattle and 'BtlUnitParameter' or 'UnitParameter')
    p.parents={['/Script/mucha.CPP_UnitParameter']=true};p.relation=1;p.effects={}
    function p:GetRelation() return self.relation end
    function p:GetContEffectList() return self.effects end
    return p
end
function effect(amount,kind,decoy)
    local e=object('Effect')
    e.class='/Script/mucha.CPP_ContFx'..(decoy and 'Decoy' or 'Avoidance')
    e.data={ParamList={amount,kind}};e.life=0
    function e:GetEffectData() return self.data end
    return e
end
menu,battle=parameter(false),parameter(true)
vm=object('VM');vm.UnitParam=menu;widget.CPP_VM_UnitParam=vm
capRow={evasionLimit=75}
function capRow:IsValid() return not self.dead end
function capRow:type() return 'UScriptStruct' end
function capRow:HasAnyFlags() error('Cannot treat native row memory as UObject') end
source=object('Table');source.class='/Script/Engine.DataTable'
schema=object('ScriptStruct /Script/mucha.UNIT_PARAMETER_CALC_DATA')
function source:GetRowStruct() return schema end
function source:FindRow(name) assert(name=='ダメージ計算用パラメータ');return capRow end
input=object('Input manager')
function input:GetDataTable(kind) assert(kind==19);return source end
systems=StaticFindObject('/Script/Engine.Default__SubsystemBlueprintLibrary')
function systems:GetWorldSubsystem(context,kind) assert(context==widget);return input end
function ready()
    drain(); assert(next(hooks)==nil)
    loaded=true;discover(widgetType);drain()
    local count=0;for _ in pairs(hooks) do count=count+1 end;assert(count==6)
end
function show(name)
    gameThread=true;hooks[cls..':'..(name or 'HandleUnitParamUpdate')](param(widget));gameThread=false
end
function values(physical,magical)
    assert(physicalLabel.value=='Phys. Eva' and magicalLabel.value=='Mag. Eva')
    assert(physicalValue.value==physical..'%' and magicalValue.value==magical..'%')
    assert(physicalLabel.visibility==3 and magicalLabel.visibility==3)
    assert(physicalValue.visibility==3 and magicalValue.visibility==3)
    assert(physicalIcon.visibility==3 and magicalIcon.visibility==3)
end
function hidden()
    assert(physicalLabel.visibility==1 and magicalLabel.visibility==1)
    assert(physicalValue.visibility==1 and magicalValue.visibility==1)
    assert(physicalIcon.visibility==1 and magicalIcon.visibility==1)
end
