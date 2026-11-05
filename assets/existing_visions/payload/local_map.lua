-- Fit the current native local-map image in the added controller view.
-- Observe native UI state by hashed object paths. No input polling, actor scans,
-- new widgets, retained HUD pointers, fog or save writes.
local config = require('config')
if config.localMap ~= 1 then return end
local runtime = {hooks={}, callbacks={}, busy=false, targets={}}
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
    local known=type(id)=='number' and id>=0
    local function choose(source,read)
        if not source then return end
        local width,height,onlyX,onlyY,count=nil,nil,nil,nil,0
        local function visit(key,value)
            key,value=unwrap(key),unwrap(value)
            local ok,x,y=pcall(read,value)
            if not ok then return end
            count=count+1;onlyX,onlyY=x,y
            if known and key==id then width,height=x,y end
        end
        if type(source)=='table' and type(source.ForEach)~='function' then
            for key,value in pairs(source) do visit(key,value) end
        else source:ForEach(visit) end
        if width and height then return width,height end
        -- Some maps are not subdivided into numbered areas. A sole native
        -- rendered/capture area is unambiguous; never guess among several.
        if not known and count==1 then return onlyX,onlyY end
    end
    local layout=vm.AreaLayoutVM
    local width,height=choose(live(layout) and layout.AreaDataMap or nil,function(value)
        return dimensions(value.Size)
    end)
    if width and height then return width,height end
    width,height=choose(capture.AreaLandCaptureDataMap,function(value)
        dimensions(value.BoxSize)
        return dimensions(vm:CorrectProjectionScale_Vector2D(value.BoxSize))
    end)
    assert(width and height,'Current local-map area is unavailable; waiting for unambiguous bounds')
    return width,height
end
local function view_mode(vm,tag)
    signature('/Script/mucha.CPP_VM_MiniMapBase:GetIsDisplay','BoolProperty')
    if not vm:GetIsDisplay() then return 2 end
    if tag==full or tag==full..'.Wide' then return 1 end
    if tag==full..'.Instance' or tag==full..'.World' or tag==full..'.Default' then return 0 end
end
local function input_ready(widget,vm)
    local subs=StaticFindObject('/Script/Engine.Default__SubsystemBlueprintLibrary')
    local kind=StaticFindObject('/Script/mucha.CPP_InputManager')
    if not live(subs) or not live(kind) or not live(vm.MiniMapDA) then return false end
    local input=subs:GetWorldSubsystem(widget,kind)
    return live(input) and input:IsEnableInput()
end
local function remember_view(widget,vm)
    signature('/Script/mucha.CPP_VM_MiniMap:GetCurrentMapId','IntProperty')
    signature('/Script/mucha.CPP_VM_MiniMap:GetCurrentAreaId','IntProperty')
    local map,area=vm:GetCurrentMapId(),vm:GetCurrentAreaId()
    local tag=vm.ViewPropertyTag.TagName:ToString()
    if type(map)~='number' or map<0 or type(area)~='number' then return tag,false end
    local key=tostring(vm:GetAddress())..':'..map..':'..area
    if key~=runtime.viewKey then
        runtime.viewKey=key;runtime.restorePending=runtime.choice~=nil
    end
    -- Loading/teardown must not replace an explicit user preference.
    if not input_ready(widget,vm) then return tag,false end
    local mode=view_mode(vm,tag)
    if mode==nil then return tag,false end
    if runtime.choice==nil then
        if mode==2 then return tag,false end
        runtime.choice=mode
    elseif runtime.restorePending then
        if mode~=runtime.choice then
            signature('/Script/mucha.CPP_VM_MiniMapBase:SetDisplayScaleIndex','IntProperty,BoolProperty')
            vm:SetDisplayScaleIndex(runtime.choice,false)
            tag=vm.ViewPropertyTag.TagName:ToString()
        end
        -- Appearance can initialize before other zone setup. The lightweight
        -- UI observer finishes restoration after input/data initialization.
        if runtime.polling then runtime.restorePending=false end
    else
        -- Every stable native state is a valid manual choice, including a
        -- direct large -> small change when the hidden notification was absent.
        runtime.choice=mode
    end
    return tag,true
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
    local path=widget:GetFullName():match('^%S+ (.+)$')
    if path then
        runtime.targets={[path]=tostring(widget:GetAddress())} -- One active field HUD.
    end
    runtime.busy=true
    local remembered,tag,ready=pcall(remember_view,widget,vm)
    runtime.busy=false
    if not remembered then
        local message=tostring(tag)
        if message~=lastError then print('[FFR local map] '..message..'\n');lastError=message end
        return
    end
    if not ready then return end
    if tag ~= full or not vm:GetIsDisplay() then
        if runtime.fitted == vm:GetAddress() then
            runtime.fitted = nil
            runtime.busy = true
            pcall(function()
                signature('/Script/mucha.CPP_VM_MiniMapBase:UpdateProperty', '')
                vm:UpdateProperty()
                -- Native property restoration can reset the display step too.
                -- Finish with the remembered step, under the reentry guard.
                local current=vm.ViewPropertyTag.TagName:ToString()
                if runtime.choice~=nil and view_mode(vm,current)~=runtime.choice then
                    signature('/Script/mucha.CPP_VM_MiniMapBase:SetDisplayScaleIndex','IntProperty,BoolProperty')
                    vm:SetDisplayScaleIndex(runtime.choice,false)
                end
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
        -- Polling observes the display step; an unchanged fit needs no native
        -- zoom writes, position resyncs or repaints on each observer tick.
        if runtime.fitted==vm:GetAddress() and runtime.fit==fit and not zoom.bSaveZoom
            and zoom.AlphaInterval.min==0 and zoom.AlphaInterval.max==0
            and zoom.ScaleInterval.min==fit and zoom.ScaleInterval.max==fit then return end
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
        runtime.fit = fit
        lastError = nil
    end)
    if not ok then
        -- Missing area data is a loading condition, not a request for the small
        -- map. Keep the native large step and retry through UI notifications.
        if runtime.fitted==vm:GetAddress() then
            runtime.fitted=nil
            pcall(function()
                signature('/Script/mucha.CPP_VM_MiniMapBase:UpdateProperty','')
                vm:UpdateProperty()
                vm:SetDisplayScaleIndex(1,false)
            end)
        end
        local message=tostring(err)
        if message~=lastError then print('[FFR local map] '..message..'\n');lastError=message end
    end
    runtime.busy = false
end
runtime.refresh = refresh
runtime.tick=function()
    for path,key in pairs(runtime.targets) do
        local widget=StaticFindObject(path)
        if live(widget) and tostring(widget:GetAddress())==key then
            runtime.polling=true
            local ok,message=pcall(refresh,widget)
            runtime.polling=false
            if not ok and tostring(message)~=lastError then
                lastError=tostring(message);print('[FFR local map] '..lastError..'\n')
            end
        else runtime.targets[path]=nil end
    end
    return false
end
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
        -- those existing widgets once; the observer retains only a hash path.
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
runtime.callbacks = {refresh,attach,runtime.discover,runtime.queued,runtime.tick}
NotifyOnNewObject('/Script/UMG.WidgetBlueprintGeneratedClass', runtime.discover)
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
if not observer then print('[FFR local map] UI observer unavailable\n') end
print('[FFR local map] Ready: minimap / full local zone / hidden\n')
