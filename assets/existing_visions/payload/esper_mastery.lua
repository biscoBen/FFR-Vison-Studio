-- Eiko's equipable esper mastery. Only native friendly espers 10451..10459
-- summoned by party Fina are eligible. No save/loadout mutation or summon grant.
local config = require('config')
if config.esperMastery ~= 1 then return end
local runtime = {states={}, callbacks={}, guarded=false, errors={}}
_G.FFRStudioEsperMastery = runtime -- UE4SS callbacks must retain a strong root.
local function log(message) print('[FFR Esper] ' .. message .. '\n') end
local function valid(o)
    return o and (type(o)=='table' or type(o)=='userdata')
        and type(o.IsValid)=='function' and o:IsValid()
end
local function each(list, fn)
    if not list then return end
    local function visit(value)
        -- UE4SS e3ba1016 push_arrayproperty(GetNonTrivialLocal) creates a
        -- Lua list whose elements are GetParam RemoteUnrealParam wrappers.
        -- The list itself is local; each value still needs get().
        if (type(value)=='table' or type(value)=='userdata') and type(value.get)=='function' then
            value=value:get()
        end
        fn(value)
    end
    if type(list)=='table' and type(list.ForEach)~='function' then
        for _,value in ipairs(list) do visit(value) end
    else list:ForEach(function(_,value) visit(value) end) end
end
local function native(name) return StaticFindObject('/Script/' .. name) end
local function safe(label, fn)
    local ok, result = pcall(fn)
    if not ok and not runtime.errors[label] then runtime.errors[label]=true; log(label .. ': ' .. tostring(result)) end
    if ok then return result end
end
local function markers(parameter)
    local found={}
    safe('active effect markers',function()
        each(parameter:GetContEffectList(), function(effect)
            if valid(effect) then found[effect:GetEffectData().ID]=true end
        end)
    end)
    -- Let the game decide which learned/equipped passives are active. MR
    -- rewards supplied by the equipped vision need no duplicate AP equip.
    safe('active passive IDs',function()
        local output={}
        parameter:GetPassiveSkillList(output)
        each(output,function(id)
            if type(id)=='number' and id>=1960 and id<=1963 then found[id*100]=true end
        end)
    end)
    return found
end
local function owner(parameter)
    local linked=parameter.m_pVisionOwner
    if valid(linked) then
        local p=linked:GetUnitParameter()
        if valid(p) and p:GetUnitId()==1003 then return linked,p end
        return nil -- A positively identified different summoner never inherits Fina's MR.
    end
    -- Native beasts do not expose a distinct summoner field. Only party Fina
    -- owns the nine original summon commands; resolve her actual battle actor.
    local battle=native('mucha.Default__CPP_BFL_Battle')
    if not valid(battle) then return nil end
    local actor=battle:GetBattleUnitByUnitId(1003,false)
    if valid(actor) then return actor,actor:GetUnitParameter() end
end
local function state(ai)
    if not valid(ai) then return nil end
    local actor=ai:GetOwnerUnit()
    if not valid(actor) then return nil end
    local parameter=actor:GetUnitParameter()
    if not valid(parameter) then return nil end
    local id=parameter:GetUnitId()
    if id<10451 or id>10459 or parameter:GetRelation()~=1 or parameter:IsDead() then return nil end
    local caster,wearer=owner(parameter)
    if not valid(caster) or not valid(wearer) then return nil end
    local key=actor:GetFullName()
    local address=actor:GetAddress()
    local s=runtime.states[key]
    -- UE4SS 3.0.1 compares Lua userdata wrappers, not their native pointers.
    -- A fresh wrapper must not grant HP/damage again or reset the extra action.
    if not s or not valid(s.actor) or s.address~=address then
        s={address=address,id=id}
        runtime.states[key]=s
    end
    s.actor=actor;s.parameter=parameter;s.ai=ai;s.caster=caster;s.wearer=wearer
    s.flags=markers(wearer)
    local vision=wearer.m_pVision
    if valid(vision) then
        local p=vision:GetUnitParameter()
        if valid(p) then
            for id in pairs(markers(p)) do s.flags[id]=true end
        end
    end
    return s
end
local function prepare(s)
    if s.flags[196000] and not s.damageApplied then
        s.damageApplied=true; s.ai:AddSkillEffect(196001)
        log('Esper damage +20%; unit=' .. s.id)
    end
    if s.flags[196200] and not s.hpApplied then
        s.hpApplied=true
        local previous=s.parameter:GetMaxHitPoint()
        s.ai:AddSkillEffect(196201)
        s.ai:AddSkillEffect(196202)
        log('Esper HP +20%; unit=' .. s.id .. '; maxHP=' .. previous .. '->' .. s.parameter:GetMaxHitPoint())
    end
end
local function original(fn)
    runtime.guarded=true
    local ok,value=pcall(fn)
    runtime.guarded=false
    if not ok then error(value) end
    return value
end
local function remaining(context)
    if runtime.guarded then return end
    return safe('remaining actions',function()
        local ai=context:get();local s=state(ai)
        if not s then return end
        prepare(s)
        local value=original(function() return ai:GetRemainingActionNumSummonedUnit() end)
        s.finalDue=value<=0
        if not s.flags[196200] then return end
        if value>0 then return value end
        local count=s.parameter:GetActionCountInBattle()
        if s.extraAt==nil then s.extraAt=count;log('Extra ordinary action; unit=' .. s.id) end
        -- Native counters may clamp at zero. Never add one indefinitely.
        if count==s.extraAt then s.finalDue=false;return 1 end
        return value
    end)
end
local function think(context)
    if runtime.guarded then return end
    return safe('ordinary action sequence',function()
        local parameter=context:get()
        local id=parameter:GetUnitId()
        if id<10451 or id>10459 then return end
        local s=state(parameter:GetOwnerBtlUnit():GetUnitAI())
        if not s then return end
        local value=original(function() return parameter:GetThinkNum() end)
        -- Repeat the opening ordinary phase once, then resume native phases.
        -- Carbuncle uses this three-phase selector instead of the return getter.
        if s.flags[196200] then value=math.max(1,value-1) end
        if s.id==10455 then s.finalDue=value%3==0 end
        return value
    end)
end
local function set_skill(context, skill)
    if runtime.guarded then return end
    safe('early special selection',function()
        local ai=context:get();local s=state(ai)
        if not s or not s.flags[196300] or s.finalDue then return end
        prepare(s)
        local count=s.parameter:GetActionCountInBattle()
        if s.rollAt~=count then
            s.rollAt=count;s.earlySpecial=nil
            s.proc=math.random(1,100)<=50
        end
        local id=skill:get()
        if id<=0 or id==431080 or id==431100 or not s.proc then return end
        -- Use each native AI's finisher slot. Carbuncle has a support finale
        -- (Glittering Ruby), rather than a damaging summon attack.
        local final=ai:GetSkillIdInSkillList(s.id==10455 and 1 or 0,s.id==10455 and 1 or 0)
        if final<=0 then error('The native esper finisher is unavailable for unit '..s.id) end
        -- The native final-special/dismissal stack is untouched. This hook only
        -- replaces ordinary SetSkill selections, once per owner action.
        s.earlySpecial=final;skill:set(final)
        log('Early special; unit=' .. s.id .. '; action=' .. count .. '; skill=' .. final)
    end)
end
local function targets(context)
    if runtime.guarded then return end
    safe('early special targets',function()
        local ai=context:get();local s=state(ai)
        if not s or not s.earlySpecial or s.rollAt~=s.parameter:GetActionCountInBattle() then return end
        original(function() ai:SetTargetRandom(s.earlySpecial) end)
    end)
end
local function random_skill(context)
    if runtime.guarded then return end
    return safe('random ordinary action selection',function()
        local ai=context:get();local s=state(ai)
        if not s or not s.flags[196300] then return end
        -- The native random helper sets m_SkillId internally, bypassing the
        -- reflected SetSkill event. Replace its stored and returned selection.
        set_skill(context,{get=function() return ai.m_SkillId end,
                           set=function(_,value) ai.m_SkillId=value end})
        targets(context)
        return ai.m_SkillId
    end)
end
local function finished(context)
    safe('esper action MP recovery',function()
        local job=context:get();local actor=job.m_pActionUnit
        if not valid(actor) then return end
        local s=state(actor:GetUnitAI())
        if not s or s.wearer:IsDead() or not s.flags[196100] or not valid(job.m_pSkill) then return end
        -- CPP_BtlSkill does not expose the interface's GetSkillId as an object
        -- method on this loader. Read the AI's reflected selection instead.
        -- Native finale stacks leave it at -1: they still count as an action.
        local skill=s.ai.m_SkillId
        if skill==431080 or skill==431100 then return end
        local count=s.parameter:GetActionCountInBattle()
        if count<=0 then return end -- No payment for a dismissed, unused summon.
        if s.paidAt==count then return end -- One payment for a multi-hit/stacked action.
        s.paidAt=count
        local ai=s.caster:GetUnitAI()
        if not valid(ai) then error('The summoner has no native battle AI.') end
        local before=s.wearer:GetMagicPoint()
        ai:AddSkillEffect(196101)
        log('Esper action recovery; unit=' .. s.id .. '; action=' .. count .. '; casterMP=' .. before .. '->' .. s.wearer:GetMagicPoint())
    end)
end
local function hook(path,pre,post)
    local callback={pre=pre,post=post};runtime.callbacks[#runtime.callbacks+1]=callback
    RegisterHook(path,pre,post)
end
safe('native hooks',function()
    hook('/Script/mucha.CPP_BtlUnitAI:GetRemainingActionNumSummonedUnit',function() end,remaining)
    hook('/Script/mucha.CPP_BtlUnitParameter:GetThinkNum',function() end,think)
    hook('/Script/mucha.CPP_BtlUnitAI:SetSkill',set_skill,targets)
    hook('/Script/mucha.CPP_BtlUnitAI:SetSkillRandom',function() end,random_skill)
    hook('/Script/mucha.CPP_BtlUnitAI:SetTargetList',function() end,targets)
    hook('/Script/mucha.CPP_BtlJobSkill:OnFinishedSkillSequence',function() end,finished)
end)
runtime.tick=function()
    safe('esper spawn scan',function()
        local seen={}
        for _,actor in ipairs(FindAllOf('CPP_BtlUnit') or {}) do
            if valid(actor) and not actor:GetFullName():find('Default__',1,true) then
                local s=state(actor:GetUnitAI())
                if s then seen[actor:GetFullName()]=true;prepare(s) end
            end
        end
        for key in pairs(runtime.states) do if not seen[key] then runtime.states[key]=nil end end
    end)
    return false
end
-- Keep this scan on the same native game-thread scheduler as presentation and
-- field controls. LoopAsync shares Lua userdata/registry state with those
-- callbacks; it must not keep entering that VM from a background thread when
-- the loader provides a game-thread loop.
runtime.queued=function() runtime.pending=nil;runtime.tick() end
runtime.loop=function()
    if runtime.pending then
        runtime.pending=runtime.pending+1
        if runtime.pending<20 then return false end
    end
    runtime.pending=0
    -- Older loaders use a single rooted bridge callback, including retries.
    if not pcall(ExecuteInGameThread,runtime.queued) then runtime.pending=nil end
    return false
end
local nativeLoop=false
if type(LoopInGameThreadWithDelay)=='function' then
    local ok,handle=pcall(LoopInGameThreadWithDelay,200,runtime.tick)
    if ok then
        nativeLoop=true;runtime.loopHandle=handle
        log('Using persistent game-thread esper loop')
    else log('Game-thread loop unavailable; using rooted callback bridge: '..tostring(handle)) end
end
if not nativeLoop then LoopAsync(200,runtime.loop) end
log('Esper mastery ready; native active rewards on Fina/equipped vision; ordinary procs preserve the final special')
