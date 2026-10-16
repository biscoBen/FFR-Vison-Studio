-- Direct battle-only presentation. SpriteStudio exposes named-part sockets;
-- use an ordinary mesh component instead of an unverified Niagara renderer.
-- This changes no actor identity, party data, gameplay events or save state.
local config = require('config').fina
if not config then return end
local states, assets, queued, failed, scans = {}, nil, false, false, 0
local function valid(o) return o ~= nil and (type(o) == 'userdata' or type(o) == 'table') and o:IsValid() end
local function name(o) return type(o) == 'string' and o or o:ToString() end
local function log(s) print('[FFR Fina] ' .. s .. '\n') end
local function native(path)
    local o = StaticFindObject('/Script/' .. path)
    assert(valid(o), 'Missing native object: ' .. path)
    return o
end
local function asset(path)
    local o = StaticFindObject(path)
    if not valid(o) then
        -- UE4SS LoadAsset queries AssetRegistry, which does not list private
        -- mod packages. Resolve the mounted package through Unreal directly.
        local kismet = native('Engine.Default__KismetSystemLibrary')
        local softPath = kismet:MakeSoftObjectPath(path)
        local reference = kismet:Conv_SoftObjPathToSoftObjRef(softPath)
        o = kismet:LoadAsset_Blocking(reference)
    end
    assert(valid(o), 'Could not load ' .. path)
    return o
end
local function vec(x, y, z) return {X=x, Y=y, Z=z} end
local function destroy(o, actor)
    if valid(o) then
        o:SetVisibility(false, true)
        -- UActorComponent explicitly accepts itself as the destruction context.
        o:K2_DestroyComponent(o)
    end
end
local function clear(s)
    destroy(s.glow, s.actor); s.glow = nil
    destroy(s.mesh, s.actor); s.mesh = nil; s.material = nil
end
local function now(sprite) return native('Engine.Default__GameplayStatics'):GetTimeSeconds(sprite) end
local function motion(s)
    -- UE4SS puts out values under the game's reflected parameter names. The
    -- supplied game/UE4SS call did not provide the assumed OutAnimationName key
    -- (the log caught the resulting nil dereference). Collect both
    -- names in one table and distinguish the verified private pack by VALUE.
    local outputs = {}
    s.sprite:GetPlayingAnimationName(outputs, outputs)
    local pack, playing, fields, ambiguous = false, nil, {}, false
    for field, value in pairs(outputs) do
        local text = name(value)
        fields[#fields + 1] = tostring(field) .. '=' .. text
        -- FName comparisons in Unreal are case-insensitive. The supplied
        -- trace reports Idle, not idle; treating it as a new action cut the
        -- full cast off at native recovery, before the turn/fire frames.
        local canonical = text:lower()
        if canonical == config.pack:lower() then pack = true
        elseif playing and playing ~= canonical then ambiguous = true
        else playing = canonical end
    end
    table.sort(fields)
    local signature = table.concat(fields, ', ')
    if #fields > 0 and not s.namesLogged then
        log('Animation output fields: ' .. signature); s.namesLogged = true
    end
    if not pack or not playing or playing == '' or playing == 'none' or ambiguous then
        -- During initialization/model changes names may be unavailable. Keep
        -- the casing alive and retry; do not tear down every battle feature.
        if s.waiting ~= signature then log('Waiting for animation names: ' .. signature); s.waiting = signature end
        return nil
    end
    s.waiting = nil
    s.playing = playing
    -- Observe the renderer, not an actor's cached animation-name property.
    return playing
end
local function create(sprite, actor, isUnit)
    -- A project can be assigned before its first animation is initialized.
    if not sprite:DoesSocketExist(FName('NULL_Crystal')) or not sprite:DoesSocketExist(FName('NULL_Aura')) then return end
    assets = {mesh=asset(config.mesh), material=asset(config.material), glow=asset(config.glow)}
    local identity = {Translation=vec(0,0,0), Rotation={X=0,Y=0,Z=0,W=1}, Scale3D=vec(1,1,1)}
    local mesh = actor:AddComponentByClass(native('Engine.StaticMeshComponent'), true, identity, false)
    assert(valid(mesh), 'Could not create the crystal mesh component')
    local s = {actor=actor, sprite=sprite, mesh=mesh, unit=isUnit, last='', logged=0}
    -- Keep a reference immediately so an initialization error can clean up.
    states[sprite:GetFullName()] = s
    mesh:SetMobility(2); mesh:SetCollisionEnabled(0); mesh:SetGenerateOverlapEvents(false); mesh:SetCastShadow(false)
    assert(mesh:SetStaticMesh(assets.mesh), 'Could not assign crystal mesh')
    s.material = mesh:CreateDynamicMaterialInstance(0, assets.material, FName('StudioFinaGlass'))
    assert(valid(s.material), 'Could not create private battle glass instance')
    s.material:SetScalarParameterValue(FName('RefractionDepthBias'), config.glassFallbackBias)
    assert(mesh:K2_AttachToComponent(sprite, FName('NULL_Crystal'), 0, 0, 0, false), 'Could not attach crystal socket')
    -- Socket translations include UUPerPixel, but socket scales do not. Match
    -- the native body ratio independently of the actor/component world scale.
    local scale = config.meshRatio * sprite.UUPerPixel
    assert(scale > 0 and scale < 100, 'Invalid SpriteStudio pixel scale')
    mesh:K2_SetRelativeLocation(vec(-config.origin.X*scale, -config.origin.Y*scale, -config.origin.Z*scale), false, {}, true)
    mesh:SetRelativeScale3D(vec(scale,scale,scale))
    mesh:SetHiddenInGame(false, true)
    log('Attached real crystal to ' .. actor:GetFullName() .. '; UUPerPixel=' .. tostring(sprite.UUPerPixel))
    return s
end
local function front_hit(triangles, dx, dy, dz, sx, sy, sz)
    -- Camera ray from the centered body through the original native LOD0.
    -- The LAST hit before the camera is its visible front surface, including
    -- overlapping/concave facets. No collision changes or physics query.
    local front = 0
    for _, t in ipairs(triangles) do
        local ax, ay, az, ex, ey, ez, fx, fy, fz = table.unpack(t)
        local px, py, pz = dy*fz-dz*fy, dz*fx-dx*fz, dx*fy-dy*fx
        local det = ex*px+ey*py+ez*pz
        if math.abs(det) > .000000001 then
            local inv = 1/det
            local tx, ty, tz = sx-ax, sy-ay, sz-az
            local u = (tx*px+ty*py+tz*pz)*inv
            if u >= -.000001 and u <= 1.000001 then
                local qx, qy, qz = ty*ez-tz*ey, tz*ex-tx*ez, tx*ey-ty*ex
                local v = (dx*qx+dy*qy+dz*qz)*inv
                if v >= -.000001 and u+v <= 1.000001 then
                    local distance = (fx*qx+fy*qy+fz*qz)*inv
                    if distance > front and distance < 1 then front = distance end
                end
            end
        end
    end
    return front > 0 and front or nil
end
local function glass(s, visible)
    if not visible then return end
    local camera = native('Engine.Default__GameplayStatics'):GetPlayerCameraManager(s.sprite, 0)
    if not valid(camera) then
        if not s.noCamera then log('Waiting for battle camera; retaining cave glass fallback'); s.noCamera = true end
        return
    end
    s.noCamera = nil
    local mathlib = native('Engine.Default__KismetMathLibrary')
    local transform = s.mesh:K2_GetComponentToWorld()
    local cameraLocal = mathlib:InverseTransformLocation(transform, camera:GetCameraLocation())
    local ox, oy, oz = config.origin.X, config.origin.Y, config.origin.Z
    local rotation = camera:GetCameraRotation()
    local pitch, yaw = math.rad(rotation.Pitch), math.rad(rotation.Yaw)
    local vx, vy, vz = math.cos(pitch)*math.cos(yaw), math.cos(pitch)*math.sin(yaw), math.sin(pitch)
    local depth = 0
    -- Sample the center column from head to feet; the bulb below her center
    -- is deeper than the middle and must not retain full-strength body warp.
    for sample=-2,2 do
        local z = sample*config.bodyHalfHeight/(2*config.meshRatio)
        local dx, dy, dz = cameraLocal.X-ox, cameraLocal.Y-oy, cameraLocal.Z-oz-z
        local hit = front_hit(config.glassTriangles, dx, dy, dz, 0, 0, z)
        if hit then
            local body = mathlib:TransformLocation(transform, vec(ox,oy,oz+z))
            local surface = mathlib:TransformLocation(transform, vec(ox+dx*hit,oy+dy*hit,oz+z+dz*hit))
            local distance = -((surface.X-body.X)*vx+(surface.Y-body.Y)*vy+(surface.Z-body.Z)*vz)
            depth = math.max(depth, distance)
        end
    end
    if depth <= 0 or depth ~= depth then return end
    -- Solve D/max(1,min(b/2,50))-b = desired body distortion.
    -- This explicitly attenuates bending at the body; distant background still
    -- reaches full refraction. It is a visual target, not a measured cave FOV.
    local amount = config.bodyRefraction
    local bias = (math.sqrt(amount*amount+8*depth)-amount)/2
    if bias < 2 then bias = math.max(0, depth-amount)
    elseif bias > 100 then bias = depth/50-amount end
    if not s.bias or math.abs(bias-s.bias) > .0001 then
        s.material:SetScalarParameterValue(FName('RefractionDepthBias'), bias); s.bias = bias
    end
    if s.glassPhase ~= s.last then
        s.glassPhase = s.last
        log('Glass ray depth=' .. depth .. '; body refraction=' .. amount .. '; bias=' .. bias
            .. '; readback=' .. s.material:K2_GetScalarParameterValue(FName('RefractionDepthBias'))
            .. '; camera FOV=' .. camera:GetFOVAngle())
    end
end
local function glow(s, frame, visible)
    -- A one-loop LB1 can reset its frame during native cleanup. Its 432-frame
    -- body finishes before the sequencer returns to idle. Once the final fade
    -- is over, destroy and latch until a NEW action, even if the frame wraps.
    if s.last == 'lb1' and frame >= config.flashes[#config.flashes][4] then s.glowFinished = true end
    local active = visible and not s.glowFinished and (s.last == 'lb1_before' or s.last == 'lb1')
    if not active then
        if valid(s.glow) then log('Glow ended at ' .. s.last .. ' frame ' .. frame .. '; removing ' .. s.glow:GetFullName()) end
        destroy(s.glow, s.actor); s.glow = nil
        return
    end
    local strength = s.last == 'lb1_before' and 1 or 0
    if s.last == 'lb1' then
        for _, interval in ipairs(config.flashes) do
            local first, full, fade, last = interval[1], interval[2], interval[3], interval[4]
            if frame >= first and frame < last then
                strength = frame < full and (frame-first)/(full-first)
                    or frame <= fade and 1 or (last-frame)/(last-fade)
                break
            end
        end
    end
    if not valid(s.glow) then
        if not valid(assets.glow) then assets.glow = asset(config.glow) end
        s.glow = native('Niagara.Default__NiagaraFunctionLibrary'):SpawnSystemAttached(
            assets.glow, s.sprite, FName('NULL_Aura'), vec(0,0,0), {Pitch=0,Yaw=0,Roll=0}, 0, true, false, 0, false)
        assert(valid(s.glow), 'Could not spawn the body glow')
        s.glow:SetAbsolute(false, false, true); s.glow:SetWorldScale3D(vec(1,1,1))
        s.glow:SetVariableVec3(FName('User.EffectPosition'), vec(0,0,0))
        s.glow:SetVariableFloat(FName('User.LightPower'), 0)
        s.glow:SetVariableFloat(FName('User.Alpha'), config.glowAlpha)
        s.glow:SetVariableFloat(FName('User.NiagaraAlpha'), strength)
        s.glow:Activate(false)
        log('Resonance glow started with ' .. s.last .. '; native frame ' .. math.floor(frame))
    end
    -- Only the initial fall has an aura. No second pulse while she is seated
    -- or when the casing returns. Native curves provide the early build-up.
    s.glow:SetVariableFloat(FName('User.NiagaraAlpha'), strength)
end
local function update(s)
    local sprite, actor = s.sprite, s.actor
    local n, time = motion(s), now(sprite)
    local visible = sprite:IsVisible() and not actor.bHidden
    if n and n ~= s.last then
        if s.logged < 12 then
            log('Native motion ' .. n .. '; frame=' .. tostring(sprite:GetPlayFrame()) .. '; rate=' .. tostring(sprite:GetPlayRate()))
            s.logged = s.logged + 1
        end
        if n == 'lb1_before' or n == 'lb1' and s.last ~= 'lb1_before' then
            s.glowFinished = false
        end
        s.last = n
    end
    local frame = sprite:GetPlayFrame()
    local observed = n or s.last
    local casing = visible and not (observed == 'lb1' and frame >= config.fall and frame < config.reform)
    s.mesh:SetVisibility(casing, true)
    -- SpriteStudio sockets expose in-plane rotation, not a full 3D spin.
    -- Rotate the actual component about its own vertical axis explicitly.
    s.mesh:K2_SetRelativeRotation({Pitch=0,Yaw=(time*config.turnRate)%360,Roll=0}, false, {}, true)
    glass(s, casing)
    glow(s, frame, visible)
end
local function tick()
    scans = scans + 1
    if scans == 1 or scans % 15 == 0 then
        for _, class in ipairs({'SsPlayerComponent', 'CPP_MuchaSsPlayerComponent'}) do
            for _, sprite in ipairs(FindAllOf(class) or {}) do
                local key = sprite:GetFullName()
                if not states[key] and valid(sprite.SsProject) and sprite.SsProject:GetFullName():find(config.project, 1, true) then
                    local actor = sprite:GetOwner()
                    -- UI renderers, map sprites and cinematics are excluded.
                    if valid(actor) then
                        local unit = actor:IsA(native('mucha.CPP_BtlUnit'))
                        if unit or actor:IsA(native('mucha.CPP_BtlSequencerSsPlayerActor')) then create(sprite, actor, unit) end
                    end
                end
            end
        end
    end
    for key, s in pairs(states) do
        if not valid(s.sprite) or not valid(s.actor) or not valid(s.sprite.SsProject)
            or not s.sprite.SsProject:GetFullName():find(config.project, 1, true) then
            clear(s); states[key] = nil
        else update(s) end
    end
end
assert(config.schema == 1, 'Unsupported Fina battle runtime config')
LoopAsync(33, function()
    if failed then return true end
    if not queued then
        queued = true
        ExecuteInGameThread(function()
            queued = false
            local ok, error = pcall(tick)
            if not ok then
                failed = true
                for _, s in pairs(states) do pcall(clear, s) end
                log('Presentation stopped: ' .. tostring(error))
            end
        end)
    end
    return false
end)
log('Battle presentation ready (body-ray refraction; single resonance glow); waiting for custom Crystal Fina')
