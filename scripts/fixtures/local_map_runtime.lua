-- A game-thread-only model of the captured Blueprint notification contract.
hooks, queued, messages, signatures = {}, {}, {}, {}
local cls = '/Game/UI/Field/MiniMap/Widget/WBP_MiniMap.WBP_MiniMap_C'
local full = 'UI.Field.MiniMap.View.Decrale'
local address = 1
function obj(value)
    value = value or {}; address=address+1; value.address=address
    function value:IsValid() return not self.invalid end
    function value:HasAnyFlags(flags) assert(flags==0x18000); return self.destroying or false end
    function value:GetAddress() return self.address end
    return value
end
function param(value) return {get=function() return value end} end
local fields = {
    ['/Script/mucha.CPP_VM_MapBase:GetIsCurrentMapField']={'BoolProperty'},
    ['/Script/mucha.CPP_VM_MiniMap:GetCurrentMapLandCaptureData']={'StructProperty'},
    ['/Script/mucha.CPP_VM_MiniMap:GetCurrentAreaId']={'IntProperty'},
    ['/Script/mucha.CPP_VM_MiniMap:GetCurrentMapId']={'IntProperty'},
    ['/Script/mucha.CPP_VM_MapBase:CorrectProjectionScale_Vector2D']={'StructProperty','StructProperty'},
    ['/Script/mucha.CPP_VM_MiniMap:GetMiniMapAppearance']={'StructProperty'},
    ['/Script/mucha.CPP_VM_MapBase:SetZoomAlpha']={'FloatProperty'},
    ['/Script/mucha.CPP_VM_MapBase:SyncPlayerData']={},
    ['/Script/mucha.CPP_VM_MiniMapBase:SetDisplayScaleIndex']={'IntProperty','BoolProperty'},
    ['/Script/mucha.CPP_VM_MiniMapBase:UpdateProperty']={},
    [cls..':SetZoomScale']={'DoubleProperty','StructProperty'},
    [cls..':SetWorldPosition']={'StructProperty'},
    [cls..':SetAppearance']={'StructProperty','DoubleProperty','DoubleProperty','DoubleProperty','DoubleProperty','FloatProperty','FloatProperty'},
}
for path,types in pairs(fields) do
    local fn=obj()
    function fn:ForEachProperty(callback)
        for index,kind in ipairs(types) do callback({GetFullName=function() return kind..' '..path..'.Arg'..index end}) end
    end
    signatures[path]=fn
end
loaded = false
function StaticFindObject(path)
    if path:sub(1,6)=='/Game/' and not loaded then return nil end
    return signatures[path]
end
function RegisterHook(path,post)
    assert(gameThread and loaded and signatures[path], 'Hook only loaded native Blueprint functions on the game thread')
    hooks[path]=post
end
function NotifyOnNewObject(path,callback)
    assert(path=='/Script/UMG.WidgetBlueprintGeneratedClass'); discover=callback
end
function ExecuteInGameThread(callback) queued[#queued+1]=callback end
function drain()
    gameThread=true
    while #queued>0 do table.remove(queued,1)() end
    gameThread=false
end
function print(s) messages[#messages+1]=s end
package.preload.config=function() return {localMap=1} end
local vmClass=obj()
vm=obj({tag=full,width=20000,height=10000,landWidth=200000,landHeight=200000,areaId=101,
    mapId=1001,projection=.1,displayX=640,displayY=640,rangeX=320,rangeY=320,
    ZoomProperty={bSaveZoom=true,AlphaInterval={min=0,max=1},ScaleInterval={min=1,max=1}}})
vm.ViewPropertyTag={TagName={ToString=function() return vm.tag end}}
function vm:GetClass() return vmClass end
function vm:GetIsCurrentMapField() assert(gameThread); return self.world or false end
function vm:GetCurrentMapId() assert(gameThread);return self.mapId end
function vm:GetCurrentAreaId() assert(gameThread);return self.areaId end
function vm:GetCurrentMapLandCaptureData()
    assert(gameThread)
    local areas=self.areas
    if areas==nil then
        areas={ForEach=function(_,callback)
            callback(param(999),param({BoxSize={X=900000,Y=800000}}))
            callback(param(101),param({BoxSize={X=self.width,Y=self.height}}))
        end}
    end
    return {LandWholeSize={X=self.landWidth,Y=self.landHeight},AreaLandCaptureDataMap=areas}
end
function vm:CorrectProjectionScale_Vector2D(size)
    assert(gameThread); return {X=size.X*self.projection,Y=size.Y*self.projection}
end
function vm:GetMiniMapAppearance()
    assert(gameThread); return {DisplaySize={X=self.displayX,Y=self.displayY},RangeSize={X=self.rangeX,Y=self.rangeY}}
end
function vm:SetZoomAlpha(alpha)
    assert(gameThread and not self.destroying); self.alpha=alpha; self.zoomCalls=(self.zoomCalls or 0)+1
    -- Native notifications can re-enter the same Blueprint callback.
    widget:SetZoomScale(self.ZoomProperty.ScaleInterval.min)
end
function vm:SyncPlayerData()
    assert(gameThread);self.syncCalls=(self.syncCalls or 0)+1
    local hook=hooks[cls..':SetWorldPosition']
    if hook then hook(param(widget),param({X=0,Y=0})) end
end
function vm:SetDisplayScaleIndex(index,animate)
    assert(gameThread and index>=0 and index<=2 and not animate)
    self.index=index;self.stepCalls=(self.stepCalls or 0)+1
    if index==0 then self.fallback=(self.fallback or 0)+1 end
    self.tag=index==2 and 'None' or index==1 and (self.world and full..'.Wide' or full) or (self.world and full..'.World' or full..'.Instance')
    local hook=hooks[cls..':SetAppearance'];if hook then hook(param(widget)) end
end
function vm:UpdateProperty()
    assert(gameThread); self.restores=(self.restores or 0)+1
    self.ZoomProperty={bSaveZoom=true,AlphaInterval={min=0,max=1},ScaleInterval={min=1,max=1}}
    self.alpha=.7; widget:SetZoomScale(1)
end
local widgetType=obj({name='WidgetBlueprintGeneratedClass '..cls})
function widgetType:GetFullName() return self.name end
widget=obj({VM_MiniMap=vm})
setmetatable(widget,{__index=function(_,key)
    if key=='MiniMapVM' then error('Use the visible Blueprint MVVM source, not the native cache') end
end})
function FindAllOf(name) assert(gameThread and name=='WBP_MiniMap_C');return {param(widget)} end
function widget:GetClass() return widgetType end
function widget:SetZoomScale(scale)
    assert(gameThread); self.paint=scale; self.paints=(self.paints or 0)+1
    local hook=hooks[cls..':SetZoomScale']; if hook then hook(param(self),param(scale)) end
end
function widget:SetWorldPosition(position)
    assert(gameThread);self.position=position
    local hook=hooks[cls..':SetWorldPosition'];if hook then hook(param(self),param(position)) end
end
function show()
    gameThread=true
    hooks[cls..':SetAppearance'](param(widget))
    gameThread=false
end
function class_name(name) widgetType.name=name end
function ready()
    drain(); assert(next(hooks)==nil)
    loaded=true; discover(widget); assert(next(hooks)==nil)
    drain(); assert(hooks[cls..':SetAppearance'] and hooks[cls..':SetZoomScale'])
    initialPaint=widget.paint
    vm.zoomCalls=nil;vm.syncCalls=nil;widget.paints=nil;widget.paint=nil
    vm.ZoomProperty={bSaveZoom=true,AlphaInterval={min=0,max=1},ScaleInterval={min=1,max=1}}
    vm.alpha=nil
    FFRStudioLocalMap.fitted=nil;FFRStudioLocalMap.choice=nil;FFRStudioLocalMap.viewKey=nil;FFRStudioLocalMap.lastMode=nil
end
