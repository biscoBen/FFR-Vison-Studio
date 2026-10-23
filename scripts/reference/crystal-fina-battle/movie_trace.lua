-- Read-only, game-thread observation. Never opens/closes/plays a movie, changes
-- the cinematic manager, loads assets or changes battle/visibility state.
local previous, emitted, pending = {}, 0, false
local function valid(o)
    return o ~= nil and (type(o) == 'userdata' or type(o) == 'table') and o:IsValid()
end
local function full(o) return valid(o) and o:GetFullName() or 'none' end
local function log(key, value, force)
    if emitted >= 1500 then return end
    if force or previous[key] ~= value then
        previous[key] = value; emitted = emitted + 1
        print('[FFR Movie] ' .. value .. '\n')
    end
end
local function observe(force)
    local players, components, managers, actors = 0, 0, 0, 0
    for _, p in ipairs(FindAllOf('ManaPlayer') or {}) do
        if valid(p) and not full(p):find('Default__', 1, true) then
            players = players + 1
            local key = 'player:' .. full(p)
            local ok, text = pcall(function()
                local c = p.ManaComponent
                -- Several public ManaPlayer getters assert that this exists.
                -- Observe the property first; never invoke them on an uninitialized player.
                if not valid(c) then return full(p) .. '; component=none; source=' .. full(p.ManaMovie) end
                components = components + 1
                local frame = tonumber(c:GetFrameNumber()) or -1
                return full(p) .. '; status=' .. tostring(p:GetStatus())
                    .. '; frameBucket=' .. tostring(math.floor(frame / 15))
                    .. '; source=' .. full(p.ManaMovie) .. '; componentMovie=' .. full(c.Movie)
                    .. '; alphaTrack=' .. tostring(c.AlphaTrack)
                    .. '; texture=' .. full(p.ManaTexture)
            end)
            log(key, ok and text or (key .. '; read unavailable: ' .. tostring(text)), force)
        end
    end
    for _, m in ipairs(FindAllOf('CPP_UI_BtlCinematicManager') or {}) do
        if valid(m) and not full(m):find('Default__', 1, true) then
            managers = managers + 1
            local ok, text = pcall(function() return full(m) .. '; bUseMovie=' .. tostring(m.bUseMovie) end)
            log('manager:' .. full(m), ok and text or ('manager read unavailable: ' .. tostring(text)), force)
        end
    end
    for _, a in ipairs(FindAllOf('BP_BtlSequencerMovieActor_C') or {}) do
        if valid(a) and not full(a):find('Default__', 1, true) then actors = actors + 1 end
    end
    log('counts', 'players=' .. players .. '; components=' .. components
        .. '; managers=' .. managers .. '; movieActors=' .. actors, force)
end
local function sample(force)
    local ok, message = pcall(observe, force)
    if not ok then log('sample-error', 'Observation unavailable: ' .. tostring(message), force) end
    return false
end
local loop = false
if type(LoopInGameThreadWithDelay) == 'function' then
    local ok = pcall(LoopInGameThreadWithDelay, 250, function() return sample(false) end)
    loop = ok
end
if not loop then
    LoopAsync(250, function()
        if pending then return false end
        pending = true
        local ok = pcall(ExecuteInGameThread, function() pending = false; sample(false) end)
        if not ok then pending = false end
        return false
    end)
end
if type(RegisterKeyBind) == 'function' and Key and Key.F8 then
    pcall(RegisterKeyBind, Key.F8, function()
        ExecuteInGameThread(function() log('bookmark', 'F8 bookmark', true); sample(true) end)
    end)
end
log('ready', 'Read-only movie observer ready; use Fina resonance once, then F8. No movie state is changed.', true)
