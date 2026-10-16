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
    if valid(o) and valid(actor) then o:K2_DestroyComponent(actor) end
end
local function clear(s)
    destroy(s.glow, s.actor); s.glow = nil; s.pulse = nil
    destroy(s.mesh, s.actor); s.mesh = nil
end
local function now(sprite) return native('Engine.Default__GameplayStatics'):GetTimeSeconds(sprite) end
local function released(n)
    return n == 'magic_attack' or n:match('^attack_') or n:match('^M_attack') or n:match('^FFBE_')
end
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
        if text == config.pack then pack = true
        elseif playing and playing ~= text then ambiguous = true
        else playing = text end
    end
    table.sort(fields)
    local signature = table.concat(fields, ', ')
    if #fields > 0 and not s.namesLogged then
        log('Animation output fields: ' .. signature); s.namesLogged = true
    end
    if not pack or not playing or playing == '' or playing == 'None' or ambiguous then
        -- During initialization/model changes names may be unavailable. Keep
        -- the casing alive and retry; do not tear down every battle feature.
        if s.waiting ~= signature then log('Waiting for animation names: ' .. signature); s.waiting = signature end
        return nil
    end
    s.waiting = nil
    s.playing = playing
    -- Observe the renderer, not an actor's cached animation-name property.
    return playing == config.cast and s.last or playing
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
    mesh:SetMaterial(0, assets.material)
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
local function glow(s, frame, visible)
    local pulse, strength = nil, 0
    if visible and s.last == 'LB1' then
        for i, interval in ipairs(config.flashes) do
            local first, peak, last = interval[1], interval[2], interval[3]
            if frame >= first and frame < last then
                pulse = i; strength = math.min((frame-first)/(peak-first), (last-frame)/(last-peak)); break
            end
        end
    end
    if pulse ~= s.pulse then
        destroy(s.glow, s.actor); s.glow = nil; s.pulse = pulse
        if pulse then
            if not valid(assets.glow) then assets.glow = asset(config.glow) end
            s.glow = native('Niagara.Default__NiagaraFunctionLibrary'):SpawnSystemAttached(
                assets.glow, s.sprite, FName('NULL_Aura'), vec(0,0,0), {Pitch=0,Yaw=0,Roll=0}, 0, true, false, 0, false)
            assert(valid(s.glow), 'Could not spawn the body glow')
            s.glow:SetAbsolute(false, false, true); s.glow:SetWorldScale3D(vec(1,1,1))
            s.glow:SetVariableFloat(FName('User.Alpha'), 0)
            s.glow:SetVariableFloat(FName('User.NiagaraAlpha'), 0)
            s.glow:Activate(false)
            log('Resonance glow ' .. pulse .. ' at native frame ' .. math.floor(frame))
        end
    end
    if valid(s.glow) then
        s.glow:SetVariableFloat(FName('User.Alpha'), strength)
        s.glow:SetVariableFloat(FName('User.NiagaraAlpha'), strength)
    end
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
        if released(n) and not s.castStart then
            s.castStart = time; log('Full cast started: ' .. config.castFrames .. ' frames')
        elseif n ~= 'idle' and n ~= 'command' and n ~= 'magic_idle' and not released(n) then
            s.castStart = nil
        end
        s.last = n
    end
    if n and s.castStart then
        local frame = math.floor((time-s.castStart)*60)
        if frame >= config.castFrames or frame < 0 or not visible then
            s.castStart = nil
            -- Restore the native current pose after the presentation finishes.
            local restore = released(n) and 'idle' or n
            if visible then assert(sprite:Play(FName(config.pack), FName(restore), 0, 1, 0, false), 'Could not restore native pose') end
            log('Full cast completed')
        else
            -- Native recovery/continuous-animation calls may restart a clip.
            -- Reapply the correct absolute frame, rather than its first pose.
            if s.playing ~= config.cast then
                assert(sprite:Play(FName(config.pack), FName(config.cast), frame, 1, 1, false), 'Native full cast unavailable')
            end
            sprite:SetPlayRate(1)
        end
    end
    local frame = sprite:GetPlayFrame()
    local observed = n or s.last
    s.mesh:SetVisibility(visible and not (observed == 'LB1' and frame >= config.fall and frame < config.reform), true)
    -- SpriteStudio sockets expose in-plane rotation, not a full 3D spin.
    -- Rotate the actual component about its own vertical axis explicitly.
    s.mesh:K2_SetRelativeRotation({Pitch=0,Yaw=(time*config.turnRate)%360,Roll=0}, false, {}, true)
    glow(s, frame, visible and n ~= nil)
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
log('Battle presentation ready (parameter-independent animation names); waiting for custom Crystal Fina')
