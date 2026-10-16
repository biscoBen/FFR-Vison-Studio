-- Executable contract fixture for documented Engine/SpriteStudio APIs.
-- It validates scope, timing and cleanup, not actual Unreal rendering.
local config = require('config').fina
messages, meshes, glows, time = {}, {}, {}, 0
local function obj(t)
    t=t or {}; t.IsValid=function(s) return not s.invalid end; return t
end
function FName(s) return {ToString=function() return s end} end
function print(s) messages[#messages+1]=s end
actor=obj({m_IsVisible=true,m_Alpha=1})
function actor:GetFullName() return 'BattleFina' end
function actor:IsA(c) return c.kind=='mucha.CPP_BtlUnit' end
function actor:IsHidden() return self.hidden or false end
local function component()
    local o=obj({visible=true})
    function o:K2_DestroyComponent(owner) assert(owner==actor); self.invalid=true end
    function o:SetVisibility(v) self.visible=v end
    function o:SetMobility(v) assert(v==2) end
    function o:SetCollisionEnabled(v) assert(v==0) end
    function o:SetGenerateOverlapEvents(v) assert(not v) end
    function o:SetCastShadow(v) assert(not v) end
    function o:SetStaticMesh(a) assert(a.path==config.mesh); return true end
    function o:SetMaterial(i,a) assert(i==0 and a.path==config.material) end
    function o:K2_AttachToComponent(parent,socket) self.parent=parent; self.socket=socket:ToString(); return true end
    function o:K2_SetRelativeLocation(v) self.location=v end
    function o:SetRelativeScale3D(v) self.scale=v end
    function o:SetHiddenInGame(v) assert(not v) end
    function o:K2_SetRelativeRotation(v) self.rotation=v end
    function o:SetAbsolute(a,b,c) assert(not a and not b and c) end
    function o:SetWorldScale3D(v) self.worldScale=v end
    function o:SetVariableFloat(k,v) self[k:ToString()]=v end
    function o:Activate(reset) assert(not reset); self.active=true end
    return o
end
function actor:AddComponentByClass(class,manual,transform,deferred)
    assert(class.kind=='Engine.StaticMeshComponent' and manual and not deferred)
    assert(transform.Scale3D.X==1 and transform.Rotation.W==1)
    local mesh=component(); meshes[#meshes+1]=mesh; return mesh
end
sprite=obj({UUPerPixel=2.7,frame=0,playing='idle'})
sprite.SsProject=obj({GetFullName=function() return 'Ss6Project '..config.project end})
function sprite:GetFullName() return 'FinaComponent' end
function sprite:GetOwner() return actor end
function sprite:DoesSocketExist(n) return n:ToString()=='NULL_Crystal' or n:ToString()=='NULL_Aura' end
function sprite:IsVisible() return true end
function sprite:GetPlayFrame() return self.frame end
function sprite:GetPlayRate() return 1 end
function sprite:SetPlayRate(rate) assert(rate==1) end
function sprite:GetPlayingAnimationName(pack,animation)
    pack.OutAnimPackName=FName(config.pack); animation.OutAnimationName=FName(self.playing)
end
function sprite:Play(pack,clip,frame,rate,loops,roundtrip)
    assert(pack:ToString()==config.pack and rate==1 and not roundtrip)
    self.playing=clip:ToString(); self.frame=frame; return true
end
local decoy=obj({SsProject=obj({GetFullName=function() return 'OtherVision' end})})
function decoy:GetFullName() return 'OtherComponent' end
function FindAllOf() return {sprite,decoy} end
local loaded = {}
function LoadAsset() error('Registry-only loader cannot resolve private mod assets') end
function StaticFindObject(path)
    if path:sub(1,8)=='/Script/' then
        local kind=path:sub(9)
        local o=obj({kind=kind})
        function o:GetTimeSeconds() return time end
        function o:MakeSoftObjectPath(path) return {path=path} end
        function o:Conv_SoftObjPathToSoftObjRef(path) return {reference=path.path} end
        function o:LoadAsset_Blocking(reference)
            local asset=obj({path=reference.reference}); loaded[reference.reference]=asset; return asset
        end
        function o:SpawnSystemAttached(asset,parent,socket,location,rotation,mode,autoDestroy,autoActivate,pool,cull)
            assert(asset.path==config.glow and parent==sprite and socket:ToString()=='NULL_Aura')
            assert(mode==0 and autoDestroy and not autoActivate and pool==0 and not cull)
            local g=component(); glows[#glows+1]=g; return g
        end
        return o
    else return loaded[path] end
end
function ExecuteInGameThread(fn) fn() end
function LoopAsync(ms,fn) assert(ms==33); tick=fn end
function run_fina_tests()
    tick(); assert(#meshes==1 and meshes[1].visible)
    assert(math.abs(meshes[1].scale.Z-.12)<.000001)
    assert(#glows==0, 'No idle aura')
    sprite.playing='command'; tick(); assert(sprite.playing=='command', 'Preparation must not fire')
    sprite.playing='magic_attack'; time=1; tick()
    assert(sprite.playing==config.cast and sprite.frame==0)
    -- Native recovery cannot truncate the approved private clip.
    sprite.playing='idle'; time=2.5; tick()
    assert(sprite.playing==config.cast and sprite.frame==90)
    sprite.playing='idle'; time=4.9; tick(); assert(sprite.playing=='idle')
    sprite.playing='LB1'; sprite.frame=120; tick(); assert(#glows==0 and meshes[1].visible)
    sprite.frame=128; tick(); assert(#glows==1 and glows[1].active)
    assert(glows[1]['User.Alpha']==.5 and meshes[1].visible)
    sprite.frame=config.fall; tick(); assert(not meshes[1].visible and glows[1]['User.Alpha']==1)
    sprite.frame=164; tick(); assert(glows[1].invalid and not meshes[1].visible)
    loaded[config.glow].invalid=true -- Reload a collected asset before its next use.
    sprite.frame=config.reform; tick(); assert(meshes[1].visible and #glows==2)
    sprite.frame=config.flashes[2][3]; tick(); assert(glows[2].invalid)
    actor.bHidden=true; tick(); assert(not meshes[1].visible)
    actor.bHidden=false; sprite.playing='idle'; tick(); assert(meshes[1].visible)
    sprite.SsProject=obj({GetFullName=function() return 'OtherVision' end}); tick()
    assert(meshes[1].invalid, 'Remove owned components when the model changes')
    assert(not table.concat(messages):find('Presentation stopped',1,true))
end
