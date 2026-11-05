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
function label()
    local o=object('Text')
    function o:SetText(text) assert(gameThread and type(text)=='table');self.value=text.text end
    function o:SetToolTipText(text) assert(gameThread and type(text)=='table');self.tooltip=text.text end
    function o:SetVisibility(value) assert(gameThread);self.visibility=value end
    return o
end
widget=object('Stat page');widgetType=object('WidgetBlueprintGeneratedClass '..cls)
function widget:GetClass() return widgetType end
widget.Text_StudioPhysicalEvasion=label();widget.Text_StudioMagicalEvasion=label()
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
    assert(widget.Text_StudioPhysicalEvasion.value=='Current Physical Evasion: '..physical..'%')
    assert(widget.Text_StudioMagicalEvasion.value=='Current Magical Evasion: '..magical..'%')
    assert(widget.Text_StudioPhysicalEvasion.visibility==3 and widget.Text_StudioMagicalEvasion.visibility==3)
end
function hidden()
    assert(widget.Text_StudioPhysicalEvasion.visibility==1 and widget.Text_StudioMagicalEvasion.visibility==1)
end
