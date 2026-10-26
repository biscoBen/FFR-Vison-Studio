-- Reflected signatures checked against the native SDK; native table effects are
-- serialized/read back separately. This fixture does not claim an in-game pass.
local function object(t)
    t=t or {};t.address=t.address or {}
    t.IsValid=function(self) return not self.invalid end
    t.GetAddress=function(self) return self.address end
    return t
end
local function context(x) return {get=function() return x end,set=function(_,v) x=v end} end
local function array(items)
    return {ForEach=function(_,fn) for i,v in ipairs(items) do fn(i,context(v)) end end}
end
hooks,messages,actors={},{},{}
function print(message) messages[#messages+1]=message end
function RegisterHook(path,pre,post) hooks[path]={pre,post} end
local function call(path,obj,body,...)
    local h=hooks[path];local args={...}
    if h then h[1](context(obj),table.unpack(args)) end
    local result=body()
    if h then local value=h[2](context(obj),table.unpack(args));if value~=nil then result=value end end
    return result
end
local function parameter(id)
    local p=object({id=id,hp=100,maxhp=100,mp=10,maxmp=100,effects={},count=0,think=1,relation=1})
    p.GetUnitId=function(self) return self.id end
    p.GetRelation=function(self) return self.relation end
    p.IsDead=function(self) return self.hp<=0 end
    p.GetContEffectList=function(self)
        local list={};for id in pairs(self.effects) do
            list[#list+1]=object({GetEffectData=function() return {ID=id} end})
        end;return array(list)
    end
    p.GetActionCountInBattle=function(self) return self.count end
    p.GetThinkNum=function(self) return call('/Script/mucha.CPP_BtlUnitParameter:GetThinkNum',self,function() return self.think end) end
    p.GetMaxHitPoint=function(self) return self.maxhp end
    p.GetMagicPoint=function(self) return self.mp end
    p.GetOwnerBtlUnit=function(self) return self.actor end
    return p
end
function actor(id,key)
    local p=parameter(id);local a=object({name=key or ('Actor'..id)})
    local ai=object({parameter=p,effectCalls={},remaining=2})
    p.actor=a;a.parameter=p;a.ai=ai
    a.GetFullName=function(self) return self.name end
    a.GetUnitParameter=function(self) return self.parameter end
    a.GetUnitAI=function(self) return self.ai end
    ai.GetOwnerUnit=function() return a.wrappers and setmetatable({}, {__index=a}) or a end
    ai.GetSkillIdInSkillList=function(_,list,index)
        assert(list==(id==10455 and 1 or 0) and index==(id==10455 and 1 or 0))
        return ({[10451]=300010,[10452]=300020,[10453]=300040,[10454]=300050,
                 [10455]=300220,[10456]=300080,[10457]=300090,[10458]=300110,[10459]=300120})[id]
    end
    ai.AddSkillEffect=function(self,id)
        self.effectCalls[id]=(self.effectCalls[id] or 0)+1
        p.effects[id]=true
        if id==196201 then p.maxhp=math.floor(p.maxhp*1.2) end
        if id==196202 then p.hp=math.min(p.maxhp,p.hp+math.floor(p.maxhp*.2)) end
        if id==196101 then p.mp=math.min(p.maxmp,p.mp+math.floor(p.maxmp*.05)) end
    end
    ai.GetRemainingActionNumSummonedUnit=function(self)
        return call('/Script/mucha.CPP_BtlUnitAI:GetRemainingActionNumSummonedUnit',self,function() return self.remaining end)
    end
    ai.SetSkill=function(self,id)
        local value=context(id)
        return call('/Script/mucha.CPP_BtlUnitAI:SetSkill',self,function() self.skill=value:get();self.m_SkillId=self.skill end,value)
    end
    ai.SetSkillRandom=function(self,index)
        assert(index==0)
        return call('/Script/mucha.CPP_BtlUnitAI:SetSkillRandom',self,function() self.m_SkillId=500020;return self.m_SkillId end,context(index))
    end
    ai.SetTargetList=function(self,list)
        call('/Script/mucha.CPP_BtlUnitAI:SetTargetList',self,function() self.targets=list end)
    end
    ai.SetTargetRandom=function(self,skill) self.targetsFor=skill end
    return a
end
fina=actor(1003)
local bfl=object({GetBattleUnitByUnitId=function(_,id,alive) assert(id==1003 and not alive);return fina end})
function StaticFindObject(path) assert(path=='/Script/mucha.Default__CPP_BFL_Battle');return bfl end
function FindAllOf(name) assert(name=='CPP_BtlUnit');return actors end
function ExecuteInGameThread(fn) fn() end
function LoopAsync(interval,callback) assert(interval==200);tick=callback end
package.preload.config=function() return {esperMastery=1} end
local function flags(...)
    fina.parameter.effects={};for _,id in ipairs({...}) do fina.parameter.effects[id]=true end
end
local function finish(a,skill)
    local job=object({m_pActionUnit=a,m_pSkill=object({GetSkillId=function() return skill end})})
    hooks['/Script/mucha.CPP_BtlJobSkill:OnFinishedSkillSequence'][2](context(job))
end
function run_tests()
    local a=actor(10452,'Ifrit');actors={fina,a}
    tick();assert(a.ai:GetRemainingActionNumSummonedUnit()==2)
    assert(next(a.ai.effectCalls)==nil)
    -- Learning a reward alone grants no effect. It must be equipped on Fina.
    a.parameter.learned={1960,1961,1962,1963};tick();assert(next(a.ai.effectCalls)==nil)
    flags(196000,196100,196200,196300);tick()
    assert(a.parameter.maxhp==120 and a.parameter.hp==120)
    assert(a.ai.effectCalls[196001]==1 and a.ai.effectCalls[196201]==1)
    a.parameter.hp=45;tick();assert(a.parameter.hp==45,'Spawn health must never repeat-heal')
    a.wrappers=true
    for _=1,8 do tick() end
    assert(a.parameter.hp==45 and a.parameter.maxhp==120,'Fresh native wrappers must not repeat the spawn bonus')
    assert(a.ai.effectCalls[196201]==1)
    -- The native counter can clamp at zero. Queries/predictions do not spend
    -- the bonus, while a later action reaches the guaranteed final stack.
    a.parameter.count=0;a.ai.remaining=2;assert(a.ai:GetRemainingActionNumSummonedUnit()==2)
    a.parameter.count=1;a.ai.remaining=1;assert(a.ai:GetRemainingActionNumSummonedUnit()==1)
    a.parameter.count=2;a.ai.remaining=0
    for _=1,8 do assert(a.ai:GetRemainingActionNumSummonedUnit()==1) end
    a.parameter.count=3;assert(a.ai:GetRemainingActionNumSummonedUnit()==0)
    -- The opening native phase is repeated, rather than adding after dismissal.
    for n,expected in ipairs({1,1,2,3}) do a.parameter.think=n;assert(a.parameter:GetThinkNum()==expected) end
    -- 50% is rolled once per action; target selection follows the new skill.
    local random=math.random;local calls=0
    math.random=function(low,high) assert(low==1 and high==100);calls=calls+1;return 50 end
    a.ai.remaining=2;a.ai:GetRemainingActionNumSummonedUnit()
    a.parameter.count=4;a.ai:SetSkill(414010);assert(a.ai.skill==300020)
    a.ai:SetSkill(500020);assert(a.ai.skill==300020 and calls==1)
    a.ai:SetTargetList({});assert(a.ai.targetsFor==300020)
    assert(a.ai:SetSkillRandom(0)==300020 and a.ai.m_SkillId==300020 and calls==1)
    a.parameter.count=5;math.random=function() calls=calls+1;return 51 end
    a.ai:SetSkill(414010);assert(a.ai.skill==414010 and calls==2)
    -- Native final stack bypasses ordinary SetSkill: always special + dismiss,
    -- regardless of earlier rolls, and never cleared/replaced by our runtime.
    a.ai.stack={300020,431100};assert(a.ai.stack[1]==300020 and a.ai.stack[2]==431100)
    math.random=random
    -- One MP payment per completed logical action, including the finale. A
    -- multi-hit sequence callback and the following dismiss are not extra pay.
    fina.parameter.mp=10;a.parameter.count=6
    finish(a,300020);finish(a,300020);finish(a,431100);assert(fina.parameter.mp==15)
    a.parameter.count=7;finish(a,414010);assert(fina.parameter.mp==20)
    fina.parameter.mp=99;a.parameter.count=8;finish(a,414010);assert(fina.parameter.mp==100)
    -- The same markers supplied through Spirit of Eiko have identical meaning;
    -- changing the equipped vision has no influence on this equipped-effect test.
    fina.parameter.vision=13110;a.parameter.count=9;fina.parameter.mp=10
    finish(a,414010);assert(fina.parameter.mp==15)
    -- No cross-owner/enemy/boss/vision effects, even with identical animations.
    local other=actor(10453,'OtherOwner');other.parameter.m_pVisionOwner=actor(1001)
    local enemy=actor(10452,'Enemy');enemy.parameter.relation=2
    local boss=actor(452,'Boss');local vision=actor(13515,'EikoVision')
    actors={fina,other,enemy,boss,vision};tick()
    for _,x in ipairs({other,enemy,boss,vision}) do assert(next(x.ai.effectCalls)==nil) end
    -- A later summon gets a fresh bonus even if names and clamped counters repeat.
    actors={fina};tick();local nextSummon=actor(10452,'Ifrit');actors={fina,nextSummon};tick()
    assert(nextSummon.parameter.maxhp==120)
    nextSummon.parameter.count=2;nextSummon.ai.remaining=0
    assert(nextSummon.ai:GetRemainingActionNumSummonedUnit()==1)
    nextSummon.parameter.count=3;assert(nextSummon.ai:GetRemainingActionNumSummonedUnit()==0)
    flags();nextSummon.parameter.count=4;fina.parameter.mp=10;finish(nextSummon,300020)
    assert(fina.parameter.mp==10)
    -- All nine native espers can proc their actual finisher slot. Even if a
    -- native final stack calls the reflected setter, it may never be rerolled.
    flags(196300)
    local rng=math.random;math.random=function() return 1 end
    for id=10451,10459 do
        local summon=actor(id,'New'..id);actors={fina,summon};tick()
        summon.ai:SetSkill(414000)
        local finisher=summon.ai:GetSkillIdInSkillList(id==10455 and 1 or 0,id==10455 and 1 or 0)
        assert(summon.ai.skill==finisher)
        summon.parameter.count=2;summon.ai.remaining=0
        if id==10455 then summon.parameter.think=3;summon.parameter:GetThinkNum()
        else summon.ai:GetRemainingActionNumSummonedUnit() end
        local nativeFinal=id==10455 and 300210 or finisher
        summon.ai:SetSkill(nativeFinal);assert(summon.ai.skill==nativeFinal,'A guaranteed finale was rerolled')
    end
    math.random=rng
    flags(196100,196200);fina.parameter.hp=0
    local survivor=actor(10452,'SurvivingEsper');actors={fina,survivor};tick()
    survivor.parameter.count=2;survivor.ai.remaining=0
    assert(survivor.ai:GetRemainingActionNumSummonedUnit()==1,'Caster KO must not remove the extra action')
    local mp=fina.parameter.mp;finish(survivor,414010);assert(fina.parameter.mp==mp)
    fina.parameter.hp=100
    assert(_G.FFRStudioEsperMastery and #_G.FFRStudioEsperMastery.callbacks==6)
end
