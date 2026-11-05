-- Reflection, out-struct and lifecycle boundaries model the pinned UE4SS API.
config={evasionStats=1}; package.preload.config=function() return config end
hooks,queue,logs={}, {}, {}; loaded=false; gameThread=false; instances={};timers={};geometryReady=true;dpi=1.5
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
 ['/Script/UMG.Widget:ForceLayoutPrepass']={},
 ['/Script/UMG.Widget:GetDesiredSize']={'StructProperty'},
 ['/Script/UMG.GridSlot:SetRow']={'IntProperty'},
 ['/Script/UMG.GridSlot:SetRowSpan']={'IntProperty'},
 ['/Script/UMG.GridSlot:SetColumn']={'IntProperty'},
 ['/Script/UMG.GridSlot:SetColumnSpan']={'IntProperty'},
 ['/Script/UMG.Widget:SetRenderTranslation']={'StructProperty'},
 ['/Script/UMG.OverlaySlot:SetPadding']={'StructProperty'},
 ['/Script/UMG.Spacer:SetSize']={'StructProperty'},
 ['/Script/UMG.Widget:SetClipping']={'EnumProperty'},
}
natives={}
function StaticFindObject(path)
    if path:sub(1,8)=='/Fixture' then return instances[path] end
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
widget=object('WBP_UnitParam_Detail_C /Fixture.StatPage');instances['/Fixture.StatPage']=widget;widgetType=object('WidgetBlueprintGeneratedClass '..cls)
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
physicalRow=panel('HorizontalBox_StudioPhysicalEvasion',{physicalIcon,physicalLabel,physicalValue})
magicalRow=panel('HorizontalBox_StudioMagicalEvasion',{magicalIcon,magicalLabel,magicalValue})
for _,row in ipairs({physicalRow,magicalRow}) do
    row.Slot=object('OverlaySlot');row.Slot.class='/Script/UMG.OverlaySlot'
    function row.Slot:SetPadding(p) assert(gameThread);self.Padding=p end
    function row:GetDesiredSize() assert(gameThread);return {X=280,Y=32} end
end
reserve=object('Spacer /Fixture.WidgetTree.Spacer_StudioEvasionRoom')
function reserve:SetSize(size) assert(gameThread);self.Size=size end
nativeEntries={};nativeCells={};nativeSpacers={};gridWrites=0
function gridSlot(name,row)
    local slot=object(name);slot.class='/Script/UMG.GridSlot'
    slot.Row=row;slot.Column=0;slot.RowSpan=1;slot.ColumnSpan=2;slot.Padding={Top=0,Bottom=0}
    function slot:SetRow(v) assert(gameThread);self.Row=v;gridWrites=gridWrites+1 end
    function slot:SetRowSpan(v) assert(gameThread);self.RowSpan=v;gridWrites=gridWrites+1 end
    function slot:SetColumn(v) assert(gameThread);self.Column=v;gridWrites=gridWrites+1 end
    function slot:SetColumnSpan(v) assert(gameThread);self.ColumnSpan=v;gridWrites=gridWrites+1 end
    return slot
end
for i,kind in ipairs({12,13,14,15,16,5,6,7,8,9,19}) do
    local e=object('Native stat '..i);e.UnitParamType=kind;e.class='/Game/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitParam_DetailEntry.WBP_UnitParam_DetailEntry_C'
    e.RenderTransform={Translation={X=0,Y=0},Scale={X=1,Y=1}}
    e.height=33
    function e:GetDesiredSize() assert(gameThread);return {X=280,Y=desiredReady==false and 0 or self.height} end
    function e:SetRenderTranslation(t) assert(gameThread);self.RenderTransform.Translation=t end
    e.Slot=gridSlot('GridSlot native '..i,2*(i-1));e.Slot.RowSpan=2
    nativeEntries[i]=e
    nativeCells[#nativeCells+1]=e
    if i<11 then
        local spacer=object('Native row spacer '..i);spacer.Size={X=0,Y=16};spacer.Visibility=0;spacer.class='/Script/UMG.Spacer'
        function spacer:GetDesiredSize() assert(gameThread);return {X=self.Size.X,Y=self.Size.Y} end
        function spacer:SetSize(v) assert(gameThread);self.Size=v;gridWrites=gridWrites+1 end
        spacer.Slot=gridSlot('GridSlot spacer '..i,2*i-1)
        nativeSpacers[#nativeSpacers+1]=spacer;nativeCells[#nativeCells+1]=spacer
    end
end
nativePanel=panel('GridPanel_28',nativeCells);nativePanel.parents={['/Script/UMG.GridPanel']=true}
function nativePanel:GetDesiredSize()
    assert(gameThread)
    local height=0
    for _,entry in ipairs(nativeEntries) do height=height+entry.height+entry.Slot.Padding.Top+entry.Slot.Padding.Bottom end
    for _,spacer in ipairs(nativeSpacers) do height=height+spacer.Size.Y+spacer.Slot.Padding.Top+spacer.Slot.Padding.Bottom end
    return {X=280,Y=height}
end
nativeWrapper=object('Native grid wrapper');nativeWrapper.GridPanel_28=nativePanel
nativeWrapper.Slot=object('Native overlay slot');nativeWrapper.Slot.Padding={Top=10};nativeWrapper.Slot.VerticalAlignment=1
nativeWrapper.EntryList={}
for i,entry in ipairs(nativeEntries) do nativeWrapper.EntryList[i]=object('DirectionGridPanelEntry '..i)
    nativeWrapper.EntryList[i].Widget=entry;nativeWrapper.EntryList[i].Spacer=nativeSpacers[i]
end
nativeWrapper.DirGridPanelProperty={GridDirection=0,SpaceBetweenLine=0,SpaceBetweenEntryInGridDirection=16}
function nativeWrapper:SetClipping(mode) assert(gameThread);self.clipping=mode end
function nativePanel:SetClipping(mode) assert(gameThread);self.clipping=mode end
widget.WBP_DirectionGridPanel=nativeWrapper
function widget:ForceLayoutPrepass() assert(gameThread);self.prepasses=(self.prepasses or 0)+1 end
root=panel('VerticalBox_StudioStats',{
    panel('Overlay_0',{nativeWrapper,physicalRow,magicalRow}),reserve})
widget.WidgetTree=object('WidgetTree');widget.WidgetTree.RootWidget=root
local overlayWidget=root.children[1]
function widget:Studio_GetRowSize(entry)
    assert(gameThread)
    if not geometryReady then return {X=0,Y=0} end
    if entry==overlayWidget then return {X=280,Y=700} end
    return {X=entry.geometry.w,Y=entry.geometry.h}
end
function widget:Studio_RowPoint(entry,origin,p)
    assert(gameThread and origin==overlayWidget)
    return {X=(entry.geometry.x+p.X*entry.geometry.scale-100)/dpi,
            Y=(entry.geometry.y+p.Y*entry.geometry.scale-200)/dpi}
end
function paint()
    local top=10
    for i,e in ipairs(nativeEntries) do
        local y=(nativeTops and nativeTops[i]) or top+e.Slot.Padding.Top
        e.geometry={kind='Geometry',x=100+e.Slot.Column*140*dpi,y=200+(y+e.RenderTransform.Translation.Y)*dpi,
            scale=dpi,w=280,h=geometryReady and 33 or 0}
        top=top+e.height+e.Slot.Padding.Top+e.Slot.Padding.Bottom+((nativeSpacers[i] and nativeSpacers[i].Size.Y) or 0)
    end
end
function native_rects()
    -- Independent unspanned SGridPanel arrangement: each grid row takes the
    -- largest desired child size plus slot padding. Read actual mutated slots.
    local heights={};local last=0
    for _,node in ipairs(nativeCells) do
        assert(node.Slot.RowSpan==1,'Normalized grid must have no spanning cells')
        local desired=node:GetDesiredSize().Y+node.Slot.Padding.Top+node.Slot.Padding.Bottom
        heights[node.Slot.Row]=math.max(heights[node.Slot.Row] or 0,desired)
        last=math.max(last,node.Slot.Row)
    end
    local offsets={};local top=10
    for row=0,last do offsets[row]=top;top=top+(heights[row] or 0) end
    local result={}
    for i,node in ipairs(nativeEntries) do
        local h=node:GetDesiredSize().Y
        result[i]={top=offsets[node.Slot.Row]+node.Slot.Padding.Top,height=h}
    end
    return result,top-10
end
function LoopInGameThreadWithDelay(ms,callback) assert(ms==100);timers[#timers+1]=callback end
function tick()
    gameThread=true;paint();FFRStudioEvasionStats.tick();gameThread=false
end
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
    gameThread=true;paint();gameThread=false
    drain(); assert(next(hooks)==nil)
    loaded=true;discover(widgetType);drain()
    local count=0;for _ in pairs(hooks) do count=count+1 end;assert(count==6)
end
function show(name)
    gameThread=true;hooks[cls..':'..(name or 'HandleUnitParamUpdate')](param(widget));gameThread=false
end
function values(physical,magical)
    assert(physicalLabel.value=='Phys. Eva.' and magicalLabel.value=='Mag. Eva.')
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
