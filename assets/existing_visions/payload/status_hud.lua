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
local asset='/Game/UI/MainMenu/Common/Key/KeyGuide/WBP_KeyGuide.WBP_KeyGuide_C'
return function(context,position)
    local controller=native('Engine.Default__GameplayStatics'):GetPlayerController(context,0)
    if not valid(controller) then return end
    local class=StaticFindObject(asset)
    if not valid(class) then class=LoadAsset(asset) end
    if not valid(class) then return end
    local widget=native('UMG.Default__WidgetBlueprintLibrary'):Create(context,class,controller)
    assert(valid(widget),'Could not create the status UserWidget')
    local ok,label=pcall(function()
        local label=widget.Text_Name
        assert(valid(label),'Status UserWidget has no text label')
        local icons=widget.WBP_DirectionGridPanel
        if valid(icons) then icons:SetVisibility(1) end -- Text includes both input guides.
        -- A key-guide's content can start hidden without native GuideData.
        -- Showing only its outer UserWidget does not show these descendants.
        local content=widget.Horizontal_Content
        assert(valid(content),'Status UserWidget has no content container')
        for _,part in ipairs({widget,content,label}) do
            part:SetVisibility(3)
            part:SetRenderOpacity(1)
        end
        -- HitTestInvisible; this indicator cannot intercept game input.
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
    function result:valid() return valid(self.widget) and valid(self.label) end
    -- UE4SS's FText parameter setter requires FText userdata. A raw Lua string
    -- can reach FText::ToFString with an invalid address instead of a Lua error.
    function result:set(value)
        self.label:SetVisibility(3)
        self.label:SetRenderOpacity(1)
        self.label:SetText(FText(value))
    end
    function result:remove()
        if valid(self.widget) then self.widget:RemoveFromParent() end
        self.widget,self.label=nil,nil
    end
    return result
end
