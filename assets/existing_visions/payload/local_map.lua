-- Fit the current native local-map image in the added controller view.
-- No input polling, new widgets, retained HUD pointers, fog or save writes.
local config = require('config')
if config.localMap ~= 1 then return end
local runtime = {hooks={}, callbacks={}, busy=false}
_G.FFRStudioLocalMap = runtime
local full = 'UI.Field.MiniMap.View.Decrale'
local widgetClass = '/Game/UI/Field/MiniMap/Widget/WBP_MiniMap.WBP_MiniMap_C'
local checked, lastError = {}, nil
local function live(o)
    return o ~= nil and (type(o)=='table' or type(o)=='userdata') and
        o:IsValid() and not o:HasAnyFlags(0x18000)
end
local function unwrap(o)
    if (type(o)=='table' or type(o)=='userdata') and type(o.get)=='function' then return o:get() end
    return o
end
local function signature(path, expected)
    if checked[path] then return end
    local fn = StaticFindObject(path)
    assert(live(fn), 'Missing map function: '..path)
    local types = {}
    fn:ForEachProperty(function(p) types[#types+1]=p:GetFullName():match('^(%w+)') end)
    assert(table.concat(types, ',') == expected, 'Unsupported map signature: '..path)
    checked[path] = true
end
local function finite(value)
    return type(value)=='number' and value==value and math.abs(value)<1e12
end
local function dimensions(vector)
    local x,y = vector.X,vector.Y
    assert(finite(x) and finite(y) and x>0 and y>0, 'Map image bounds are unavailable')
    return x,y
end
local function area_dimensions(vm,capture)
    signature('/Script/mucha.CPP_VM_MiniMap:GetCurrentAreaId','IntProperty')
    local id=vm:GetCurrentAreaId()
    assert(type(id)=='number' and id>=0,'Current local-map area is unavailable')
    -- Fit the geometry supplied to the visible area layout. It is already in
    -- projected UI units; applying world/projection conversion again shrinks it.
    local layout=vm.AreaLayoutVM
    local rendered=live(layout) and layout.AreaDataMap or nil
    local width,height
    local function rendered_area(key,value)
        if unwrap(key)==id then width,height=dimensions(unwrap(value).Size) end
    end
    if rendered then
        if type(rendered)=='table' and type(rendered.ForEach)~='function' then
            for key,value in pairs(rendered) do rendered_area(key,value) end
        else rendered:ForEach(rendered_area) end
    end
    if width and height then return width,height end
    local areas=capture.AreaLandCaptureDataMap
    assert(areas~=nil,'Current local-map capture areas are unavailable')
    local function visit(key,value)
        if unwrap(key)~=id then return end
        local area=unwrap(value)
        -- Image origin is the active area's WorldLocation (native
        -- CPP_VM_MiniMap override), not the whole land group's center.
        -- Read its BoxSize while the returned struct/map entry is alive.
        dimensions(area.BoxSize)
        width,height=dimensions(vm:CorrectProjectionScale_Vector2D(area.BoxSize))
    end
    if type(areas)=='table' and type(areas.ForEach)~='function' then
        for key,value in pairs(areas) do visit(key,value) end
    else areas:ForEach(visit) end
    assert(width and height,'Current area has no local-map capture bounds')
    return width,height
end
local function refresh(context)
    if runtime.busy then return end
    local widget = unwrap(context)
    if not live(widget) or not live(widget:GetClass()) or
        widget:GetClass():GetFullName() ~= 'WidgetBlueprintGeneratedClass '..widgetClass then return end
    -- This is the actual MVVM source bound by WBP_MiniMap, not the separate
    -- native MiniMapVM cache, which can be absent or point at an older source.
    local vm = widget.VM_MiniMap
    if not live(vm) or not live(vm:GetClass()) then return end
    if vm.ViewPropertyTag.TagName:ToString() ~= full then
        if runtime.fitted == vm:GetAddress() then
            runtime.fitted = nil
            runtime.busy = true
            pcall(function()
                signature('/Script/mucha.CPP_VM_MiniMapBase:UpdateProperty', '')
                vm:UpdateProperty()
            end)
            runtime.busy = false
        end
        return
    end
    runtime.busy = true
    local ok,err = pcall(function()
        signature('/Script/mucha.CPP_VM_MapBase:GetIsCurrentMapField', 'BoolProperty')
        if vm:GetIsCurrentMapField() then return end
        signature('/Script/mucha.CPP_VM_MiniMap:GetCurrentMapLandCaptureData', 'StructProperty')
        signature('/Script/mucha.CPP_VM_MapBase:CorrectProjectionScale_Vector2D', 'StructProperty,StructProperty')
        signature('/Script/mucha.CPP_VM_MiniMap:GetMiniMapAppearance', 'StructProperty')
        signature('/Script/mucha.CPP_VM_MapBase:SetZoomAlpha', 'FloatProperty')
        signature('/Script/mucha.CPP_VM_MapBase:SyncPlayerData', '')
        signature(widgetClass..':SetZoomScale', 'DoubleProperty,StructProperty')
        local capture = vm:GetCurrentMapLandCaptureData()
        local width,height = area_dimensions(vm,capture)
        -- SetAppearance sizes the map's masked viewport from DisplaySize.
        -- RangeSize belongs to the smaller range-ring image inside that view.
        local rx,ry = dimensions(vm:GetMiniMapAppearance().DisplaySize)
        -- A diagonal fits even when the native local minimap rotates, and in
        -- either circular or rectangular masks. Leave room for edge markers.
        local fit = 0.90 * math.min(rx,ry) / math.sqrt(width*width + height*height)
        assert(finite(fit) and fit>=0.000001 and fit<=100, 'Unsupported local-map scale')
        local zoom = vm.ZoomProperty
        zoom.bSaveZoom = false
        zoom.AlphaInterval.min,zoom.AlphaInterval.max = 0,0
        zoom.ScaleInterval.min,zoom.ScaleInterval.max = fit,fit
        vm:SetZoomAlpha(0)
        -- An area transition can change fit while alpha is already zero.
        -- Resync native UI coordinates too, keeping the image/player/markers
        -- together instead of repainting only their render scale.
        vm:SyncPlayerData()
        -- Field notifications may suppress an unchanged zero alpha. Paint the
        -- same native widget through its own Blueprint setter in that case.
        widget:SetZoomScale(fit)
        runtime.fitted = vm:GetAddress()
        lastError = nil
    end)
    if not ok then
        -- Do not leave a misleading enlarged crop when bounds are unavailable.
        pcall(function()
            signature('/Script/mucha.CPP_VM_MiniMapBase:SetDisplayScaleIndex', 'IntProperty,BoolProperty')
            if live(vm) then vm:SetDisplayScaleIndex(0,false) end
        end)
        local message = tostring(err)
        if message ~= lastError then print('[FFR local map] '..message..'\n'); lastError=message end
    end
    runtime.busy = false
end
runtime.refresh = refresh
local function attach()
    local added=false
    for _,name in ipairs({'SetAppearance','SetZoomScale','SetWorldPosition'}) do
        local path = widgetClass..':'..name
        local fn = StaticFindObject(path)
        if live(fn) and runtime.hooks[path] ~= fn:GetAddress() then
            -- Non-native RegisterHook callbacks run AFTER the Blueprint body.
            -- Hook the real widget notifications: native C++ input handlers can
            -- bypass ProcessEvent and are not reliable hook points.
            local ok = pcall(function()
                RegisterHook(path, refresh)
                runtime.hooks[path] = fn:GetAddress()
                added=true
            end)
            if not ok then print('[FFR local map] Map view hook unavailable: '..name..'\n') end
        end
    end
    if added then
        -- The first map can initialize before the queued hooks attach. Refresh
        -- those existing widgets once; never retain them or poll the HUD.
        local widgets=FindAllOf('WBP_MiniMap_C')
        if widgets then
            if type(widgets)=='table' and type(widgets.ForEach)~='function' then
                for _,widget in ipairs(widgets) do refresh(unwrap(widget)) end
            else widgets:ForEach(function(_,widget) refresh(unwrap(widget)) end) end
        end
    end
end
runtime.attach = attach
runtime.queued=function() runtime.pending=false;attach() end
runtime.discover = function()
    -- Construction can occur off-thread. Carry no object pointer to this work.
    if runtime.pending then return end
    runtime.pending=true
    ExecuteInGameThread(runtime.queued)
end
runtime.callbacks = {refresh,attach,runtime.discover,runtime.queued}
NotifyOnNewObject('/Script/UMG.WidgetBlueprintGeneratedClass', runtime.discover)
ExecuteInGameThread(attach)
print('[FFR local map] Ready: minimap / full local zone / hidden\n')
