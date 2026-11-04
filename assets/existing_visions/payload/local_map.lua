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
local function refresh(context)
    if runtime.busy then return end
    local widget = unwrap(context)
    if not live(widget) or not live(widget:GetClass()) or
        widget:GetClass():GetFullName() ~= 'WidgetBlueprintGeneratedClass '..widgetClass then return end
    local vm = widget.MiniMapVM
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
        signature(widgetClass..':SetZoomScale', 'DoubleProperty,StructProperty')
        local capture = vm:GetCurrentMapLandCaptureData()
        dimensions(capture.LandWholeSize)
        local size = vm:CorrectProjectionScale_Vector2D(capture.LandWholeSize)
        local width,height = dimensions(size)
        local rx,ry = dimensions(vm:GetMiniMapAppearance().RangeSize)
        -- A diagonal fits even when the native local minimap rotates, and in
        -- either circular or rectangular masks. Leave room for edge markers.
        local fit = 0.90 * math.min(rx,ry) / math.sqrt(width*width + height*height)
        assert(finite(fit) and fit>=0.000001 and fit<=100, 'Unsupported local-map scale')
        local zoom = vm.ZoomProperty
        zoom.bSaveZoom = false
        zoom.AlphaInterval.min,zoom.AlphaInterval.max = 0,0
        zoom.ScaleInterval.min,zoom.ScaleInterval.max = fit,fit
        vm:SetZoomAlpha(0)
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
    for _,name in ipairs({'SetAppearance','SetZoomScale'}) do
        local path = widgetClass..':'..name
        local fn = StaticFindObject(path)
        if live(fn) and runtime.hooks[path] ~= fn:GetAddress() then
            -- Non-native RegisterHook callbacks run AFTER the Blueprint body.
            -- Hook the real widget notifications: native C++ input handlers can
            -- bypass ProcessEvent and are not reliable hook points.
            local ok = pcall(function()
                RegisterHook(path, refresh)
                runtime.hooks[path] = fn:GetAddress()
            end)
            if not ok then print('[FFR local map] Map view hook unavailable: '..name..'\n') end
        end
    end
end
runtime.attach = attach
runtime.discover = function()
    -- Construction can occur off-thread. Carry no object pointer to this work.
    ExecuteInGameThread(attach)
end
runtime.callbacks = {refresh,attach,runtime.discover}
NotifyOnNewObject('/Script/mucha.CPP_WBP_MiniMap', runtime.discover)
ExecuteInGameThread(attach)
print('[FFR local map] Ready: minimap / full local zone / hidden\n')
