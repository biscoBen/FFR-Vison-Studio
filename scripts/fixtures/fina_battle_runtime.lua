-- Executable contract fixture for documented Engine/SpriteStudio APIs.
-- It validates scope, timing and cleanup, not actual Unreal rendering.
local config = require('config').fina
messages, meshes, glows, materials, time = {}, {}, {}, {}, 0
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
    function o:CreateDynamicMaterialInstance(i,a,label)
        assert(i==0 and a.path==config.material and label:ToString()=='StudioFinaGlass')
        local m=obj({source=a})
        function m:SetScalarParameterValue(key,value) self[key:ToString()]=value end
        materials[#materials+1]=m; return m
    end
    function o:K2_GetComponentScale()
        local p=sprite.parentScale or {X=1,Y=1,Z=1}
        return {X=self.scale.X*p.X,Y=self.scale.Y*p.Y,Z=self.scale.Z*p.Z}
    end
    function o:K2_AttachToComponent(parent,socket) self.parent=parent; self.socket=socket:ToString(); return true end
    function o:K2_SetRelativeLocation(v) self.location=v end
    function o:SetRelativeScale3D(v) self.scale=v end
    function o:SetHiddenInGame(v) assert(not v) end
    function o:K2_SetRelativeRotation(v) self.rotation=v end
    function o:SetAbsolute(a,b,c) assert(not a and not b and c) end
    function o:SetWorldScale3D(v) self.worldScale=v end
    function o:SetVariableFloat(k,v) self[k:ToString()]=v end
    function o:SetVariableVec3(k,v) self[k:ToString()]=v end
    function o:Activate(reset) assert(not reset); self.active=true; self.activationAlpha=self['User.NiagaraAlpha'] end
    return o
end
function actor:AddComponentByClass(class,manual,transform,deferred)
    assert(class.kind=='Engine.StaticMeshComponent' and manual and not deferred)
    assert(transform.Scale3D.X==1 and transform.Rotation.W==1)
    local mesh=component(); meshes[#meshes+1]=mesh; return mesh
end
sprite=obj({UUPerPixel=2.7,frame=0,playing='Idle'})
sprite.SsProject=obj({GetFullName=function() return 'Ss6Project '..config.project end})
function sprite:GetFullName() return 'FinaComponent' end
function sprite:GetOwner() return actor end
function sprite:DoesSocketExist(n) return n:ToString()=='NULL_Crystal' or n:ToString()=='NULL_Aura' end
function sprite:IsVisible() return true end
function sprite:GetPlayFrame() return self.frame end
function sprite:GetPlayRate() return 1 end
function sprite:SetPlayRate(rate) assert(rate==1) end
function sprite:GetPlayingAnimationName(pack,animation)
    -- UE4SS names these fields from the game's UFunction, not upstream's
    -- header. The supplied log proves OutAnimationName was absent. These
    -- synthetic renamed parameters reproduce that contract without claiming
    -- to know the game's exact private spelling.
    if self.namesUnavailable then return end
    local fields = self.outputFields or {'GamePack', 'GameClip'}
    pack[fields[1]]=FName(config.pack); animation[fields[2]]=FName(self.playing)
end
function sprite:Play(pack,clip,frame,rate,loops,roundtrip)
    error('Presentation must not override native action playback or hit timing')
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
    sprite.playing='magic_idle'; sprite.frame=1; tick()
    assert(sprite.playing=='magic_idle' and sprite.frame==1)
    sprite.frame=29; time=.5; tick()
    sprite.playing='magic_attack'; sprite.frame=1; time=.516; tick()
    assert(sprite.playing=='magic_attack' and sprite.frame==1)
    sprite.playing='Idle'; sprite.frame=3; time=1.032; tick()
    assert(sprite.playing=='Idle' and sprite.frame==3, 'Native recovery must stay intact')
    sprite.playing='lb1_before'; sprite.frame=1; tick()
    assert(#glows==1 and glows[1].active and meshes[1].visible, 'Warm up during preparation')
    assert(glows[1]['User.Alpha']==config.glowAlpha and glows[1]['User.NiagaraAlpha']==1)
    assert(glows[1]['User.EffectPosition'].Z==0 and glows[1]['User.LightPower']==0)
    sprite.playing='LB1'; sprite.frame=0; tick()
    sprite.frame=100; tick()
    assert(#glows==1 and glows[1]['User.NiagaraAlpha']==1 and meshes[1].visible, 'Fully bright before falling')
    sprite.frame=config.fall; tick(); assert(not meshes[1].visible and glows[1]['User.NiagaraAlpha']==1)
    sprite.frame=config.fall+15; tick(); assert(glows[1]['User.NiagaraAlpha']==.5)
    sprite.frame=183; tick(); assert(not glows[1].invalid and glows[1]['User.NiagaraAlpha']==0)
    sprite.frame=config.reform-30; tick()
    assert(#glows==1 and glows[1]['User.NiagaraAlpha']==.5, 'Reuse warm particles for reformation')
    sprite.frame=config.reform; tick(); assert(meshes[1].visible and glows[1]['User.NiagaraAlpha']==1)
    sprite.frame=config.flashes[2][4]; tick(); assert(glows[1].invalid, 'Destroy immediately after final fade')
    -- Native cleanup can reset the frame, or expose a stale/missing name.
    -- Neither may restart the first flash on the returning battle actor.
    sprite.frame=0; tick(); assert(#glows==1)
    sprite.namesUnavailable=true; tick(); sprite.namesUnavailable=false; tick(); assert(#glows==1)
    sprite.frame=20; tick(); assert(#glows==1)
    actor.bHidden=true; tick(); assert(not meshes[1].visible and glows[1].invalid)
    actor.bHidden=false; sprite.playing='idle'; tick(); assert(meshes[1].visible)
    -- Direct entry (without preparation) must also light immediately, and an
    -- interrupted resonance must not leave its aura behind in idle/damage.
    sprite.playing='LB1'; sprite.frame=0; tick(); assert(#glows==2 and glows[2]['User.NiagaraAlpha']==1)
    sprite.playing='damage'; tick(); assert(glows[2].invalid)
    -- A later real preparation must reset the completion latch normally.
    sprite.playing='lb1_before'; sprite.frame=1; tick(); assert(#glows==3 and glows[3].active)
    sprite.playing='LB1'; sprite.frame=config.flashes[2][4]; tick(); assert(glows[3].invalid)
    sprite.frame=0; tick(); assert(#glows==3)
    sprite.SsProject=obj({GetFullName=function() return 'OtherVision' end}); tick()
    assert(meshes[1].invalid, 'Remove owned components when the model changes')
    assert(not table.concat(messages):find('Presentation stopped',1,true))
end
