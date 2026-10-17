-- Reflection contract fixture, not a substitute for a live Unreal trace.
messages, callbacks, keybinds, classes, reads = {}, {}, {}, {}, 0
local gameThread = false
function print(s) messages[#messages+1] = s end
function FName(s) return {ToString=function() return s end} end
function obj(label, data)
    data = data or {}
    function data:IsValid() return not self.invalid end
    function data:GetFullName() assert(gameThread); return label end
    return data
end
function arr(values)
    return {ForEach=function(_, fn)
        assert(gameThread)
        for i,v in ipairs(values) do fn(i, {get=function() return v end}) end
    end}
end
function FindAllOf(class) assert(gameThread); reads=reads+1; return classes[class] or {} end
function LoopAsync(interval, fn) assert(interval==100); loop=fn end
function ExecuteInGameThread(fn) callbacks[#callbacks+1]=fn end
function RegisterKeyBind(key, fn) keybinds[key]=fn end
Key={F8=8,F9=9}
function RegisterHook() error('No native hooks allowed') end
function LoadAsset() error('No asset loads allowed') end
function sample()
    assert(not gameThread)
    loop()
    local pending=callbacks; callbacks={}
    gameThread=true
    for _,fn in ipairs(pending) do fn() end
    gameThread=false
end
function contains(fragment)
    for _,s in ipairs(messages) do if s:find(fragment,1,true) then return true end end
    return false
end
function count(fragment)
    local result=0
    for _,s in ipairs(messages) do if s:find(fragment,1,true) then result=result+1 end end
    return result
end
function setup_battle()
    sprite=obj('SsPlayerComponent TestSprite', {SsProject=obj('Ss6Project OriginalProject'),playing='Idle',frame=0,rate=1})
    function sprite:GetPlayingAnimationName(a,b)
        assert(gameThread)
        a.GamePack=FName('NativePack'); b.GameMotion=FName(self.playing)
    end
    actor=obj('CPP_BtlUnit TestUnit', {m_pSsPlayerComponent=sprite,m_AnimationName=FName('idle'),m_IsVisible=true})
    function actor:K2_GetActorLocation() assert(gameThread); return {X=1,Y=-500,Z=100} end
    skill=obj('CPP_BtlSkill TestSkill', {id=500270})
    function skill:GetSkillId() assert(gameThread); return self.id end
    sequence=obj('LevelSequenceActor NativeSequence', {LevelSequenceAsset=obj('LevelSequence /Game/OriginalMaster')})
    player=obj('LevelSequencePlayer NativePlayer', {playing=true})
    function player:IsPlaying() assert(gameThread); return self.playing end
    function sequence:GetSequencePlayer() assert(gameThread); return player end
    effect=obj('NiagaraComponent NativeEffect', {Asset=obj('NiagaraSystem /Game/OriginalFX'),active=true})
    function effect:IsActive() assert(gameThread); return self.active end
    function effect:GetOwner() assert(gameThread); return actor end
    function effect:K2_GetComponentLocation() assert(gameThread); return {X=2,Y=-500,Z=125} end
    job=obj('CPP_BtlJobSkill TestJob', {m_pSkill=skill,m_pLevelSequenceActor=sequence,
        m_ActionUnitList=arr({actor}),m_TargetUnitList=arr({actor}),
        m_GeneratedNiagaraDatas=arr({{NiagaraID=FName('FX1'),NiagaraComponent=effect}}),
        m_GeneratedSpriteStudioDatas=arr({{spriteStudioID=FName('SS1'),ssActor=actor}})})
    manager=obj('CPP_BtlJobManager BattleJobs',{m_WorkingJobList=arr({job}),m_WaitingJobList=arr({})})
    classes={CPP_BtlUnit={actor},CPP_BtlJobManager={manager},LevelSequenceActor={sequence},NiagaraComponent={effect}}
end
