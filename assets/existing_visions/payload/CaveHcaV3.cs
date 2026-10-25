/* vgmstream HCA v3 algorithm reference license:
Copyright (c) 2008-2025 Adam Gashlin, Fastelbja, Ronny Elfert, bnnm,
                        Christopher Snowhill, NicknineTheEagle, bxaimc,
                        Thealexbarney, CyberBotX, EdnessP, et al

Portions Copyright (c) 2004-2008, Marko Kreen
Portions Copyright 2001-2007  jagarl / Kazunori Ueno <jagarl@creator.club.ne.jp>
Portions Copyright (c) 1998, Justin Frankel/Nullsoft Inc.
Portions Copyright (C) 2006 Nullsoft, Inc.
Portions Copyright (c) 2005-2007 Paul Hsieh
Portions Copyright (C) 2000-2004 Leshade Entis, Entis-soft.
Portions Public Domain originating with Sun Microsystems

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
*/
// HCA v3 independent-channel preview decoder. Uses the existing MIT VGAudio
// coefficient tables and IMDCT; v3 resolution/noise rules follow vgmstream's
// clhca.c (https://github.com/vgmstream/vgmstream, src/coding/libs/clhca.c).
// Deliberately reject stereo coupling/HFR rather than decode them as HCA v2.
using System;
using System.IO;
using System.Reflection;
using VGAudio.Codecs.CriHca;
using VGAudio.Utilities;

namespace FfrStudio
{
    public static class CaveHcaV3
    {
        static T Table<T>(string name)
        {
            Type t = typeof(CriHcaFrame).Assembly.GetType("VGAudio.Codecs.CriHca.CriHcaTables", true);
            return (T)t.GetProperty(name, BindingFlags.Static | BindingFlags.Public).GetValue(null, null);
        }
        static readonly byte[] Bits = Table<byte[]>("QuantizedSpectrumMaxBits");
        static readonly byte[][] CodeBits = Table<byte[][]>("QuantizedSpectrumBits");
        static readonly sbyte[][] CodeValues = Table<sbyte[][]>("QuantizedSpectrumValue");
        static readonly double[] Scales = Table<double[]>("DequantizerScalingTable");
        static readonly double[] Steps = Table<double[]>("QuantizerStepSize");
        static readonly byte[] ResolutionCurve = {
            14,14,14,14,14,14,13,13,13,13,13,13,12,12,12,12,12,12,11,11,11,11,11,11,
            10,10,10,10,10,10,10,9,9,9,9,9,9,8,8,8,8,8,8,7,6,6,5,4,4,4,3,3,3,2,2,2,
            2,1,1,1,1,1,1,1,1,1
        };

        static int BE(byte[] b, int p, int n)
        {
            int value = 0;
            for (int i = 0; i < n; i++) value = checked(value * 256 + b[p + i]);
            return value;
        }
        static void Require(bool valid, string message)
        {
            if (!valid) throw new InvalidDataException(message);
        }
        static int Read(BitReader reader, int count)
        {
            Require(reader.Position + count <= reader.LengthBits - 16, "Incomplete HCA v3 frame.");
            return reader.ReadInt(count);
        }
        static void ScaleFactors(CriHcaChannel channel, BitReader reader)
        {
            int bits = Read(reader, 3), count = channel.CodedScaleFactorCount;
            if (bits == 0) { Array.Clear(channel.ScaleFactors, 0, 128); return; }
            int value = Read(reader, 6);
            channel.ScaleFactors[0] = value;
            for (int i = 1; i < count; i++)
            {
                if (bits >= 6) value = Read(reader, 6);
                else
                {
                    int delta = Read(reader, bits), escape = (1 << bits) - 1;
                    value = delta == escape ? Read(reader, 6) : value + delta - (escape >> 1);
                    Require(value >= 0 && value < 64, "Invalid HCA v3 scale factor.");
                }
                channel.ScaleFactors[i] = value;
            }
        }
        static int[] Resolution(CriHcaChannel channel, int noise, int boundary, int min, int max)
        {
            int[] indexes = new int[130]; // noise from front, valid coefficients from back
            int noises = 0, valid = 0;
            for (int i = 0; i < channel.CodedScaleFactorCount; i++)
            {
                int scale = channel.ScaleFactors[i], resolution = 0;
                if (scale > 0)
                {
                    int position = noise - (i < boundary ? 1 : 0) + 1 - ((5 * scale) >> 1);
                    resolution = position < 0 ? 15 : position <= 65 ? ResolutionCurve[position] : 0;
                    resolution = Math.Max(min, Math.Min(max, resolution));
                    if (resolution == 0) indexes[noises++] = i;
                    else indexes[127 - valid++] = i;
                }
                channel.Resolution[i] = resolution;
                channel.Gain[i] = Scales[scale] * Steps[resolution];
            }
            indexes[128] = noises; indexes[129] = valid;
            return indexes;
        }
        static void Spectra(CriHcaChannel channel, BitReader reader, int subframe)
        {
            double[] spectra = channel.Spectra[subframe];
            Array.Clear(spectra, 0, 128);
            for (int i = 0; i < channel.CodedScaleFactorCount; i++)
            {
                int resolution = channel.Resolution[i], bits = Bits[resolution];
                // A prefix lookup may peek into the checksum; only the shorter
                // selected code is consumed. Validate that consumed span below.
                Require(reader.Position + bits <= reader.LengthBits, "Incomplete HCA v3 coefficients.");
                int code = reader.PeekInt(bits), value;
                if (resolution < 8)
                {
                    bits = CodeBits[resolution][code]; value = CodeValues[resolution][code];
                }
                else
                {
                    value = (code >> 1) * (1 - ((code & 1) << 1));
                    if (value == 0) bits--;
                }
                reader.Position += bits;
                spectra[i] = value * channel.Gain[i];
            }
        }
        static void Noise(CriHcaChannel channel, int[] indexes, int subframe, ref uint random)
        {
            int noises = indexes[128], valid = indexes[129];
            if (valid == 0) return;
            for (int i = 0; i < noises; i++)
            {
                random = unchecked(0x343FD * random + 0x269EC3);
                int source = indexes[128 - valid + (int)((((random >> 16) & 0x7FFF) * valid) >> 15)];
                int target = indexes[i];
                int scale = Math.Max(0, channel.ScaleFactors[target] - channel.ScaleFactors[source] + 62);
                // clHCA's table has one leading zero and unity at index 63.
                double gain = scale == 0 ? 0 : Math.Pow(2, (scale - 63) * 53.0 / 128);
                channel.Spectra[subframe][target] = gain * channel.Spectra[subframe][source];
            }
        }

        public static byte[] Decode(byte[] raw)
        {
            Require(raw.Length >= 64 && BE(raw, 0, 4) == 0x48434100 && BE(raw, 4, 2) == 0x300,
                "Expected decrypted HCA v3 cave recording.");
            int header = BE(raw, 6, 2);
            Require(header >= 48 && header <= raw.Length && BE(raw, 8, 4) == 0x666D7400 && BE(raw, 24, 4) == 0x636F6D70,
                "Unsupported HCA v3 header.");
            int channels = raw[12], rate = BE(raw, 13, 3), frames = BE(raw, 16, 4);
            int delay = BE(raw, 20, 2), padding = BE(raw, 22, 2), size = BE(raw, 28, 2);
            int min = raw[30], max = raw[31], bands = raw[34];
            Require(channels >= 1 && channels <= 2 && rate == 48000 && frames > 0 && frames <= 512 && size >= 8,
                "Unsupported HCA v3 preview size or channels.");
            Require(raw[32] == 1 && raw[33] <= 1 && bands >= 1 && bands <= 128 && raw[35] == bands &&
                raw[36] == 0 && raw[37] == 0 && raw[38] == 0 && raw[39] == 0 && min <= 1 && max >= min && max <= 15,
                "HCA v3 preview needs independent channels without HFR or MS stereo.");
            // trim_hca removes the loop; decrypt clears ciph before calling this.
            Require(BE(raw, 40, 4) == 0x63697068 && BE(raw, 44, 2) == 0 &&
                raw.Length == header + frames * size, "HCA v3 preview needs complete, decrypted one-shot frames.");
            int samples = checked(frames * 1024 - delay - padding);
            Require(samples > 0 && samples <= 480000, "Invalid HCA v3 preview duration.");
            Crc16 crc = new Crc16(0x8005);
            Require(crc.Compute(raw, header - 2) == BE(raw, header - 2, 2), "Invalid HCA v3 header checksum.");
            HcaInfo info = new HcaInfo { ChannelCount = channels, TrackCount = 1, ChannelConfig = raw[33],
                TotalBandCount = bands, BaseBandCount = bands, SampleRate = rate };
            CriHcaFrame frame = new CriHcaFrame(info);
            byte[] pcm = new byte[samples * channels * 2]; uint random = 1;
            for (int index = 0; index < frames; index++)
            {
                byte[] encoded = new byte[size]; Array.Copy(raw, header + index * size, encoded, 0, size);
                Require(crc.Compute(encoded, size - 2) == BE(encoded, size - 2, 2), "Invalid HCA v3 frame checksum.");
                BitReader reader = new BitReader(encoded);
                Require(Read(reader, 16) == 65535, "Invalid HCA v3 sync.");
                int noise = Read(reader, 9), boundary = Read(reader, 7);
                int[][] indexes = new int[channels][];
                for (int channel = 0; channel < channels; channel++)
                {
                    ScaleFactors(frame.Channels[channel], reader);
                    indexes[channel] = Resolution(frame.Channels[channel], noise, boundary, min, max);
                }
                for (int sf = 0; sf < 8; sf++)
                    foreach (CriHcaChannel channel in frame.Channels) Spectra(channel, reader, sf);
                // Correct v3 unpacking ends in zero padding. Older rules silently
                // consume the wrong bits here and still produce a plausible WAV.
                Require(reader.Position <= size * 8 - 16, "HCA v3 coefficient overread.");
                for (int bit = reader.Position; bit < size * 8 - 16; bit++)
                    Require((encoded[bit >> 3] & (1 << (7 - (bit & 7)))) == 0, "HCA v3 frame has unread audio coefficients.");
                for (int sf = 0; sf < 8; sf++)
                {
                    for (int c = 0; c < channels; c++)
                    {
                        CriHcaChannel channel = frame.Channels[c];
                        if (min == 0) Noise(channel, indexes[c], sf, ref random);
                        channel.Mdct.RunImdct(channel.Spectra[sf], channel.PcmFloat[sf]);
                        for (int i = 0; i < 128; i++)
                        {
                            int position = index * 1024 + sf * 128 + i - delay;
                            if (position < 0 || position >= samples) continue;
                            int value = (int)(channel.PcmFloat[sf][i] * 32768);
                            short sample = (short)Math.Max(-32768, Math.Min(32767, value));
                            int offset = (position * channels + c) * 2;
                            pcm[offset] = (byte)sample; pcm[offset + 1] = (byte)(sample >> 8);
                        }
                    }
                }
            }
            using (MemoryStream stream = new MemoryStream())
            using (BinaryWriter writer = new BinaryWriter(stream))
            {
                writer.Write(System.Text.Encoding.ASCII.GetBytes("RIFF")); writer.Write(pcm.Length + 36);
                writer.Write(System.Text.Encoding.ASCII.GetBytes("WAVEfmt ")); writer.Write(16);
                writer.Write((short)1); writer.Write((short)channels); writer.Write(rate);
                writer.Write(rate * channels * 2); writer.Write((short)(channels * 2)); writer.Write((short)16);
                writer.Write(System.Text.Encoding.ASCII.GetBytes("data")); writer.Write(pcm.Length); writer.Write(pcm);
                return stream.ToArray();
            }
        }
    }
}
