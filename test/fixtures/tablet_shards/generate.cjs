// Synthetic data only. Node's AES implementation is independent of the Dart decoder.
const fs=require('node:fs'), crypto=require('node:crypto');
const root=__dirname+'/';
const cat=(...a)=>Buffer.concat(a), b=n=>Buffer.from([n]), i=n=>{let x=Buffer.alloc(4);x.writeInt32LE(n);return x;};
const u16=n=>{let x=Buffer.alloc(2);x.writeUInt16LE(n);return x;}, i64=n=>{let x=Buffer.alloc(8);x.writeBigInt64LE(n);return x;};
const f=n=>{let x=Buffer.alloc(4);x.writeFloatLE(n);return x;};
const str=(s,wide=false)=>{let x=Buffer.from(s+'\0',wide?'utf16le':'latin1');return cat(i(wide?-x.length/2:x.length),x);};
const type=(name,...args)=>cat(str(name),i(args.length),...args);
const int=type('IntProperty'), bool=type('BoolProperty'), struct=name=>type('StructProperty',type(name));
const tag=(name,ty,data,flags=0)=>cat(str(name,name==='Player'),ty,i(data.length),b(flags),flags&1?i(0):Buffer.alloc(0),flags&2?Buffer.alloc(16):Buffer.alloc(0),flags&4?cat(b(2),Buffer.alloc(17)):Buffer.alloc(0),data);
const props=(...tags)=>cat(...tags,str('None'));
const record=(uid,open,id=-1)=>props(tag('ID',int,i(id)),tag('UniqueID',int,i(uid)),tag('IsOpen',bool,Buffer.alloc(0),open?16:0));
const area=records=>props(tag('treasureBox',struct('MapTreasureBox'),props(tag('treasureBoxList',type('ArrayProperty',struct('TreasureBoxRecord')),cat(i(records.length),...records)))));
const entries=[
 [3140,[record(10,false),record(10,true,25004),record(11,true),record(11,true),record(9999,true)]],
 [2120,[record(10,true),record(11,false)]],[2015,[]],[3031,[record(0,true)]],
 [3211,[record(3,true),record(4,false)]],[2040,[record(9,true),record(8,false)]],
 [9999,[record(4,true)]]
];
const map=tag('Map',struct('MapSaveData'),props(tag('mapGimmick',type('MapProperty',int,struct('MapGimmick')),cat(i(0),i(entries.length),...entries.map(([id,records])=>cat(i(id),area(records)))))));
const player=tag('Player',struct('PlayerSaveData'),props(tag('PlayTime',type('FloatProperty'),f(12345)),tag('SavedDateTime',struct('DateTime'),i64(638976312000000000n)),tag('UnusedPlayerText',type('TextProperty'),Buffer.from([17,22,33]))));
const header=version=>cat(Buffer.from('GVAS'),i(version),i(522),i(1000),u16(5),u16(6),u16(0),i(1234),str('Engine テスト',true),i(3),i(1),Buffer.alloc(16),i(1),str('/Script/FFRS.SaveData'),b(0));
const encode=plain=>{plain=cat(plain,Buffer.alloc((16-plain.length%16)%16));const aes=crypto.createCipheriv('aes-256-ecb',Buffer.from('wwrqPkdwzPvgfchQ8kTYHVbn4umTf3d7'),null);aes.setAutoPadding(false);return cat(Buffer.from('SVHD'),Buffer.alloc(28),aes.update(plain),aes.final());};
const unused=tag('UnrelatedInventory',type('FutureProperty'),Buffer.from([55,44,33]),7);
fs.writeFileSync(root+'partial.sav',encode(cat(header(3),props(unused,map,player))));
fs.writeFileSync(root+'unsupported-version.sav',encode(cat(header(4),props(map,player))));
fs.writeFileSync(root+'missing-map.sav',encode(cat(header(3),props(player))));
// The named Map tag deliberately claims a negative payload size.
fs.writeFileSync(root+'invalid-size.sav',encode(cat(header(3),str('Map'),struct('MapSaveData'),i(-1),b(0))));
fs.writeFileSync(root+'README.txt','Synthetic Resonance save fixtures, created using Node crypto AES-256-ECB. No player saves or game assets.\nPartial fixture: 5 known shards; duplicate/open/closed/unrelated IDs, zero actor ID, empty visited map, partly visited Fina maps, UTF-16 names, GUID/index/extension tag flags, unknown unrelated fields.\n');
