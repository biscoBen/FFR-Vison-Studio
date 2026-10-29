-- A separate, game-created UserWidget. Never construct raw UWidgets, copy live
-- Slate font structs, or attach children to the game's changing HUD tree.
local function valid(o)
    return o~=nil and (type(o)=='userdata' or type(o)=='table') and o:IsValid()
end
local function native(name)
    local o=StaticFindObject('/Script/'..name)
    assert(valid(o),'Native HUD object unavailable: '..name)
    return o
end
local asset='/Game/UI/Studio/WBP_StudioStatus.WBP_StudioStatus_C'
return function(context,position)
    local controller=native('Engine.Default__GameplayStatics'):GetPlayerController(context,0)
    if not valid(controller) then return end
    local class=StaticFindObject(asset)
    if not valid(class) then
        -- UE4SS LoadAsset only queries AssetRegistry. Private mod packages are
        -- mounted in IoStore but absent from that registry. Use the same native
        -- soft-object loader as Fina's private presentation assets.
        local kismet=native('Engine.Default__KismetSystemLibrary')
        local path=kismet:MakeSoftObjectPath(asset)
        class=kismet:LoadAsset_Blocking(kismet:Conv_SoftObjPathToSoftObjRef(path))
    end
    assert(valid(class),'Could not load the private Studio status widget: '..asset)
    local widget=native('UMG.Default__WidgetBlueprintLibrary'):Create(context,class,controller)
    assert(valid(widget),'Could not create the status UserWidget')
    local ok,label=pcall(function()
        local label=widget.Text_Name
        assert(valid(label),'Status UserWidget has no text label')
        -- This private passive UserWidget has one plain TextBlock. It has no
        -- key-guide icons, input subscriptions, bindings, animation or tick.
        widget:AddToViewport(50)
        widget:SetAnchorsInViewport({Minimum={X=position.anchorX,Y=position.anchorY},
            Maximum={X=position.anchorX,Y=position.anchorY}})
        widget:SetAlignmentInViewport({X=position.anchorX,Y=position.anchorY})
        widget:SetDesiredSizeInViewport({X=position.width or 520,Y=40})
        widget:SetPositionInViewport({X=position.x,Y=position.y},false)
        return label
    end)
    if not ok then widget:RemoveFromParent();error(label) end
    local result={widget=widget,label=label,controller=controller,context=context}
    function result:valid() return valid(self.widget) and valid(self.label) and valid(self.controller) end
    function result:show()
        for _,part in ipairs({self.widget,self.label}) do
            if part:GetVisibility()~=3 then part:SetVisibility(3) end
            if part:GetRenderOpacity()~=1 then part:SetRenderOpacity(1) end
        end
        if self.text and self.label:GetText():ToString()~=self.value then self.label:SetText(self.text) end
    end
    -- UE4SS's FText parameter setter requires FText userdata. A raw Lua string
    -- can reach FText::ToFString with an invalid address instead of a Lua error.
    function result:set(value)
        self.text=FText(value);self.value=value
        self:show()
    end
    function result:remove()
        if valid(self.widget) then self.widget:RemoveFromParent() end
        self.widget,self.label,self.text,self.value=nil,nil,nil,nil
    end
    result:show()
    return result
end
