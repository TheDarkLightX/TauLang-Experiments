// Generated from the checked Tau expression tree; experimental optimizer.
pub const SPEC_HASH: [u8; 32] = [107, 211, 242, 142, 147, 128, 56, 163, 99, 24, 45, 1, 193, 55, 31, 47, 76, 253, 212, 135, 103, 125, 226, 212, 116, 227, 220, 10, 68, 150, 244, 235];
fn shift_left(a:u32,b:u32)->u32 { if b >= 32 {0} else { (a << (b as u32)) & 4294967295u32 } }
fn shift_right(a:u32,b:u32)->u32 { if b >= 32 {0} else { a >> (b as u32) } }
#[allow(unused_parens)]
pub fn tau_step32(input:&[u32;102])->[u32;21] {
    let value0: bool = ((input[64] as u32) > 0u32);
    let value1: bool = ((input[64] as u32) <= 32u32);
    let value2: bool = (value0 && value1);
    let value3: bool = ((input[81] as u32) <= 16u32);
    let value4: bool = (value2 && value3);
    let value5: bool = ((input[100] as u32) <= (input[81] as u32));
    let value6: bool = (value4 && value5);
    let value7: bool = ((input[83] as u32) < (input[64] as u32));
    let value8: bool = (value6 && value7);
    let value9: bool = ((input[101] as u32) == 0u32);
    let value10: bool = (value8 && value9);
    if value10 {
        let value11: u32 = ((input[83] as u32) ^ 0u32);
        let value12: u32 = core::cmp::min(value11, 1u32);
        let value13: u32 = (value12).wrapping_sub(1u32);
        let value14: u32 = ((input[0] as u32) & value13);
        let value15: u32 = ((input[83] as u32) ^ 1u32);
        let value16: u32 = core::cmp::min(value15, 1u32);
        let value17: u32 = (value16).wrapping_sub(1u32);
        let value18: u32 = ((input[2] as u32) & value17);
        let value19: u32 = (value14 | value18);
        let value20: u32 = ((input[83] as u32) ^ 2u32);
        let value21: u32 = core::cmp::min(value20, 1u32);
        let value22: u32 = (value21).wrapping_sub(1u32);
        let value23: u32 = ((input[4] as u32) & value22);
        let value24: u32 = (value19 | value23);
        let value25: u32 = ((input[83] as u32) ^ 3u32);
        let value26: u32 = core::cmp::min(value25, 1u32);
        let value27: u32 = (value26).wrapping_sub(1u32);
        let value28: u32 = ((input[6] as u32) & value27);
        let value29: u32 = (value24 | value28);
        let value30: u32 = ((input[83] as u32) ^ 4u32);
        let value31: u32 = core::cmp::min(value30, 1u32);
        let value32: u32 = (value31).wrapping_sub(1u32);
        let value33: u32 = ((input[8] as u32) & value32);
        let value34: u32 = (value29 | value33);
        let value35: u32 = ((input[83] as u32) ^ 5u32);
        let value36: u32 = core::cmp::min(value35, 1u32);
        let value37: u32 = (value36).wrapping_sub(1u32);
        let value38: u32 = ((input[10] as u32) & value37);
        let value39: u32 = (value34 | value38);
        let value40: u32 = ((input[83] as u32) ^ 6u32);
        let value41: u32 = core::cmp::min(value40, 1u32);
        let value42: u32 = (value41).wrapping_sub(1u32);
        let value43: u32 = ((input[12] as u32) & value42);
        let value44: u32 = (value39 | value43);
        let value45: u32 = ((input[83] as u32) ^ 7u32);
        let value46: u32 = core::cmp::min(value45, 1u32);
        let value47: u32 = (value46).wrapping_sub(1u32);
        let value48: u32 = ((input[14] as u32) & value47);
        let value49: u32 = (value44 | value48);
        let value50: u32 = ((input[83] as u32) ^ 8u32);
        let value51: u32 = core::cmp::min(value50, 1u32);
        let value52: u32 = (value51).wrapping_sub(1u32);
        let value53: u32 = ((input[16] as u32) & value52);
        let value54: u32 = (value49 | value53);
        let value55: u32 = ((input[83] as u32) ^ 9u32);
        let value56: u32 = core::cmp::min(value55, 1u32);
        let value57: u32 = (value56).wrapping_sub(1u32);
        let value58: u32 = ((input[18] as u32) & value57);
        let value59: u32 = (value54 | value58);
        let value60: u32 = ((input[83] as u32) ^ 10u32);
        let value61: u32 = core::cmp::min(value60, 1u32);
        let value62: u32 = (value61).wrapping_sub(1u32);
        let value63: u32 = ((input[20] as u32) & value62);
        let value64: u32 = (value59 | value63);
        let value65: u32 = ((input[83] as u32) ^ 11u32);
        let value66: u32 = core::cmp::min(value65, 1u32);
        let value67: u32 = (value66).wrapping_sub(1u32);
        let value68: u32 = ((input[22] as u32) & value67);
        let value69: u32 = (value64 | value68);
        let value70: u32 = ((input[83] as u32) ^ 12u32);
        let value71: u32 = core::cmp::min(value70, 1u32);
        let value72: u32 = (value71).wrapping_sub(1u32);
        let value73: u32 = ((input[24] as u32) & value72);
        let value74: u32 = (value69 | value73);
        let value75: u32 = ((input[83] as u32) ^ 13u32);
        let value76: u32 = core::cmp::min(value75, 1u32);
        let value77: u32 = (value76).wrapping_sub(1u32);
        let value78: u32 = ((input[26] as u32) & value77);
        let value79: u32 = (value74 | value78);
        let value80: u32 = ((input[83] as u32) ^ 14u32);
        let value81: u32 = core::cmp::min(value80, 1u32);
        let value82: u32 = (value81).wrapping_sub(1u32);
        let value83: u32 = ((input[28] as u32) & value82);
        let value84: u32 = (value79 | value83);
        let value85: u32 = ((input[83] as u32) ^ 15u32);
        let value86: u32 = core::cmp::min(value85, 1u32);
        let value87: u32 = (value86).wrapping_sub(1u32);
        let value88: u32 = ((input[30] as u32) & value87);
        let value89: u32 = (value84 | value88);
        let value90: u32 = ((input[83] as u32) ^ 16u32);
        let value91: u32 = core::cmp::min(value90, 1u32);
        let value92: u32 = (value91).wrapping_sub(1u32);
        let value93: u32 = ((input[32] as u32) & value92);
        let value94: u32 = (value89 | value93);
        let value95: u32 = ((input[83] as u32) ^ 17u32);
        let value96: u32 = core::cmp::min(value95, 1u32);
        let value97: u32 = (value96).wrapping_sub(1u32);
        let value98: u32 = ((input[34] as u32) & value97);
        let value99: u32 = (value94 | value98);
        let value100: u32 = ((input[83] as u32) ^ 18u32);
        let value101: u32 = core::cmp::min(value100, 1u32);
        let value102: u32 = (value101).wrapping_sub(1u32);
        let value103: u32 = ((input[36] as u32) & value102);
        let value104: u32 = (value99 | value103);
        let value105: u32 = ((input[83] as u32) ^ 19u32);
        let value106: u32 = core::cmp::min(value105, 1u32);
        let value107: u32 = (value106).wrapping_sub(1u32);
        let value108: u32 = ((input[38] as u32) & value107);
        let value109: u32 = (value104 | value108);
        let value110: u32 = ((input[83] as u32) ^ 20u32);
        let value111: u32 = core::cmp::min(value110, 1u32);
        let value112: u32 = (value111).wrapping_sub(1u32);
        let value113: u32 = ((input[40] as u32) & value112);
        let value114: u32 = (value109 | value113);
        let value115: u32 = ((input[83] as u32) ^ 21u32);
        let value116: u32 = core::cmp::min(value115, 1u32);
        let value117: u32 = (value116).wrapping_sub(1u32);
        let value118: u32 = ((input[42] as u32) & value117);
        let value119: u32 = (value114 | value118);
        let value120: u32 = ((input[83] as u32) ^ 22u32);
        let value121: u32 = core::cmp::min(value120, 1u32);
        let value122: u32 = (value121).wrapping_sub(1u32);
        let value123: u32 = ((input[44] as u32) & value122);
        let value124: u32 = (value119 | value123);
        let value125: u32 = ((input[83] as u32) ^ 23u32);
        let value126: u32 = core::cmp::min(value125, 1u32);
        let value127: u32 = (value126).wrapping_sub(1u32);
        let value128: u32 = ((input[46] as u32) & value127);
        let value129: u32 = (value124 | value128);
        let value130: u32 = ((input[83] as u32) ^ 24u32);
        let value131: u32 = core::cmp::min(value130, 1u32);
        let value132: u32 = (value131).wrapping_sub(1u32);
        let value133: u32 = ((input[48] as u32) & value132);
        let value134: u32 = (value129 | value133);
        let value135: u32 = ((input[83] as u32) ^ 25u32);
        let value136: u32 = core::cmp::min(value135, 1u32);
        let value137: u32 = (value136).wrapping_sub(1u32);
        let value138: u32 = ((input[50] as u32) & value137);
        let value139: u32 = (value134 | value138);
        let value140: u32 = ((input[83] as u32) ^ 26u32);
        let value141: u32 = core::cmp::min(value140, 1u32);
        let value142: u32 = (value141).wrapping_sub(1u32);
        let value143: u32 = ((input[52] as u32) & value142);
        let value144: u32 = (value139 | value143);
        let value145: u32 = ((input[83] as u32) ^ 27u32);
        let value146: u32 = core::cmp::min(value145, 1u32);
        let value147: u32 = (value146).wrapping_sub(1u32);
        let value148: u32 = ((input[54] as u32) & value147);
        let value149: u32 = (value144 | value148);
        let value150: u32 = ((input[83] as u32) ^ 28u32);
        let value151: u32 = core::cmp::min(value150, 1u32);
        let value152: u32 = (value151).wrapping_sub(1u32);
        let value153: u32 = ((input[56] as u32) & value152);
        let value154: u32 = (value149 | value153);
        let value155: u32 = ((input[83] as u32) ^ 29u32);
        let value156: u32 = core::cmp::min(value155, 1u32);
        let value157: u32 = (value156).wrapping_sub(1u32);
        let value158: u32 = ((input[58] as u32) & value157);
        let value159: u32 = (value154 | value158);
        let value160: u32 = ((input[83] as u32) ^ 30u32);
        let value161: u32 = core::cmp::min(value160, 1u32);
        let value162: u32 = (value161).wrapping_sub(1u32);
        let value163: u32 = ((input[60] as u32) & value162);
        let value164: u32 = (value159 | value163);
        let value165: u32 = ((input[83] as u32) ^ 31u32);
        let value166: u32 = core::cmp::min(value165, 1u32);
        let value167: u32 = (value166).wrapping_sub(1u32);
        let value168: u32 = ((input[62] as u32) & value167);
        let value169: u32 = (value164 | value168);
        let value170: bool = (value169 == 0u32);
        let value171: u32 = ((input[1] as u32) & value13);
        let value172: u32 = ((input[3] as u32) & value17);
        let value173: u32 = (value171 | value172);
        let value174: u32 = ((input[5] as u32) & value22);
        let value175: u32 = (value173 | value174);
        let value176: u32 = ((input[7] as u32) & value27);
        let value177: u32 = (value175 | value176);
        let value178: u32 = ((input[9] as u32) & value32);
        let value179: u32 = (value177 | value178);
        let value180: u32 = ((input[11] as u32) & value37);
        let value181: u32 = (value179 | value180);
        let value182: u32 = ((input[13] as u32) & value42);
        let value183: u32 = (value181 | value182);
        let value184: u32 = ((input[15] as u32) & value47);
        let value185: u32 = (value183 | value184);
        let value186: u32 = ((input[17] as u32) & value52);
        let value187: u32 = (value185 | value186);
        let value188: u32 = ((input[19] as u32) & value57);
        let value189: u32 = (value187 | value188);
        let value190: u32 = ((input[21] as u32) & value62);
        let value191: u32 = (value189 | value190);
        let value192: u32 = ((input[23] as u32) & value67);
        let value193: u32 = (value191 | value192);
        let value194: u32 = ((input[25] as u32) & value72);
        let value195: u32 = (value193 | value194);
        let value196: u32 = ((input[27] as u32) & value77);
        let value197: u32 = (value195 | value196);
        let value198: u32 = ((input[29] as u32) & value82);
        let value199: u32 = (value197 | value198);
        let value200: u32 = ((input[31] as u32) & value87);
        let value201: u32 = (value199 | value200);
        let value202: u32 = ((input[33] as u32) & value92);
        let value203: u32 = (value201 | value202);
        let value204: u32 = ((input[35] as u32) & value97);
        let value205: u32 = (value203 | value204);
        let value206: u32 = ((input[37] as u32) & value102);
        let value207: u32 = (value205 | value206);
        let value208: u32 = ((input[39] as u32) & value107);
        let value209: u32 = (value207 | value208);
        let value210: u32 = ((input[41] as u32) & value112);
        let value211: u32 = (value209 | value210);
        let value212: u32 = ((input[43] as u32) & value117);
        let value213: u32 = (value211 | value212);
        let value214: u32 = ((input[45] as u32) & value122);
        let value215: u32 = (value213 | value214);
        let value216: u32 = ((input[47] as u32) & value127);
        let value217: u32 = (value215 | value216);
        let value218: u32 = ((input[49] as u32) & value132);
        let value219: u32 = (value217 | value218);
        let value220: u32 = ((input[51] as u32) & value137);
        let value221: u32 = (value219 | value220);
        let value222: u32 = ((input[53] as u32) & value142);
        let value223: u32 = (value221 | value222);
        let value224: u32 = ((input[55] as u32) & value147);
        let value225: u32 = (value223 | value224);
        let value226: u32 = ((input[57] as u32) & value152);
        let value227: u32 = (value225 | value226);
        let value228: u32 = ((input[59] as u32) & value157);
        let value229: u32 = (value227 | value228);
        let value230: u32 = ((input[61] as u32) & value162);
        let value231: u32 = (value229 | value230);
        let value232: u32 = ((input[63] as u32) & value167);
        let value233: u32 = (value231 | value232);
        let value234: bool = (value233 == 0u32);
        let value235: bool = (value170 && value234);
        let value236: bool = ((input[100] as u32) == (input[81] as u32));
        let value237: bool = (value235 && value236);
        if value237 {
            [((input[82] as u32)), ((input[83] as u32)), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (1u32), (0u32)]
        } else {
            let value238: bool = (value169 == 1u32);
            if value238 {
                let value239: u32 = ((input[83] as u32)).wrapping_add(1u32);
                [(value233), (value239), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
            } else {
                let value240: bool = (value169 == 2u32);
                if value240 {
                    let value241: u32 = ((input[82] as u32)).wrapping_add(value233);
                    let value242: u32 = ((input[83] as u32)).wrapping_add(1u32);
                    [(value241), (value242), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                } else {
                    let value243: bool = (value169 == 3u32);
                    if value243 {
                        let value244: u32 = ((input[82] as u32)).wrapping_sub(value233);
                        let value245: u32 = ((input[83] as u32)).wrapping_add(1u32);
                        [(value244), (value245), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                    } else {
                        let value246: bool = (value169 == 4u32);
                        if value246 {
                            let value247: u32 = ((input[82] as u32) ^ value233);
                            let value248: u32 = ((input[83] as u32)).wrapping_add(1u32);
                            [(value247), (value248), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                        } else {
                            let value249: bool = (value169 == 5u32);
                            let value250: bool = (value233 < 16u32);
                            let value251: bool = (value249 && value250);
                            if value251 {
                                let value252: u32 = (value233 ^ 0u32);
                                let value253: u32 = core::cmp::min(value252, 1u32);
                                let value254: u32 = (value253).wrapping_sub(1u32);
                                let value255: u32 = ((input[84] as u32) & value254);
                                let value256: u32 = (value233 ^ 1u32);
                                let value257: u32 = core::cmp::min(value256, 1u32);
                                let value258: u32 = (value257).wrapping_sub(1u32);
                                let value259: u32 = ((input[85] as u32) & value258);
                                let value260: u32 = (value255 | value259);
                                let value261: u32 = (value233 ^ 2u32);
                                let value262: u32 = core::cmp::min(value261, 1u32);
                                let value263: u32 = (value262).wrapping_sub(1u32);
                                let value264: u32 = ((input[86] as u32) & value263);
                                let value265: u32 = (value260 | value264);
                                let value266: u32 = (value233 ^ 3u32);
                                let value267: u32 = core::cmp::min(value266, 1u32);
                                let value268: u32 = (value267).wrapping_sub(1u32);
                                let value269: u32 = ((input[87] as u32) & value268);
                                let value270: u32 = (value265 | value269);
                                let value271: u32 = (value233 ^ 4u32);
                                let value272: u32 = core::cmp::min(value271, 1u32);
                                let value273: u32 = (value272).wrapping_sub(1u32);
                                let value274: u32 = ((input[88] as u32) & value273);
                                let value275: u32 = (value270 | value274);
                                let value276: u32 = (value233 ^ 5u32);
                                let value277: u32 = core::cmp::min(value276, 1u32);
                                let value278: u32 = (value277).wrapping_sub(1u32);
                                let value279: u32 = ((input[89] as u32) & value278);
                                let value280: u32 = (value275 | value279);
                                let value281: u32 = (value233 ^ 6u32);
                                let value282: u32 = core::cmp::min(value281, 1u32);
                                let value283: u32 = (value282).wrapping_sub(1u32);
                                let value284: u32 = ((input[90] as u32) & value283);
                                let value285: u32 = (value280 | value284);
                                let value286: u32 = (value233 ^ 7u32);
                                let value287: u32 = core::cmp::min(value286, 1u32);
                                let value288: u32 = (value287).wrapping_sub(1u32);
                                let value289: u32 = ((input[91] as u32) & value288);
                                let value290: u32 = (value285 | value289);
                                let value291: u32 = (value233 ^ 8u32);
                                let value292: u32 = core::cmp::min(value291, 1u32);
                                let value293: u32 = (value292).wrapping_sub(1u32);
                                let value294: u32 = ((input[92] as u32) & value293);
                                let value295: u32 = (value290 | value294);
                                let value296: u32 = (value233 ^ 9u32);
                                let value297: u32 = core::cmp::min(value296, 1u32);
                                let value298: u32 = (value297).wrapping_sub(1u32);
                                let value299: u32 = ((input[93] as u32) & value298);
                                let value300: u32 = (value295 | value299);
                                let value301: u32 = (value233 ^ 10u32);
                                let value302: u32 = core::cmp::min(value301, 1u32);
                                let value303: u32 = (value302).wrapping_sub(1u32);
                                let value304: u32 = ((input[94] as u32) & value303);
                                let value305: u32 = (value300 | value304);
                                let value306: u32 = (value233 ^ 11u32);
                                let value307: u32 = core::cmp::min(value306, 1u32);
                                let value308: u32 = (value307).wrapping_sub(1u32);
                                let value309: u32 = ((input[95] as u32) & value308);
                                let value310: u32 = (value305 | value309);
                                let value311: u32 = (value233 ^ 12u32);
                                let value312: u32 = core::cmp::min(value311, 1u32);
                                let value313: u32 = (value312).wrapping_sub(1u32);
                                let value314: u32 = ((input[96] as u32) & value313);
                                let value315: u32 = (value310 | value314);
                                let value316: u32 = (value233 ^ 13u32);
                                let value317: u32 = core::cmp::min(value316, 1u32);
                                let value318: u32 = (value317).wrapping_sub(1u32);
                                let value319: u32 = ((input[97] as u32) & value318);
                                let value320: u32 = (value315 | value319);
                                let value321: u32 = (value233 ^ 14u32);
                                let value322: u32 = core::cmp::min(value321, 1u32);
                                let value323: u32 = (value322).wrapping_sub(1u32);
                                let value324: u32 = ((input[98] as u32) & value323);
                                let value325: u32 = (value320 | value324);
                                let value326: u32 = (value233 ^ 15u32);
                                let value327: u32 = core::cmp::min(value326, 1u32);
                                let value328: u32 = (value327).wrapping_sub(1u32);
                                let value329: u32 = ((input[99] as u32) & value328);
                                let value330: u32 = (value325 | value329);
                                let value331: u32 = ((input[83] as u32)).wrapping_add(1u32);
                                [(value330), (value331), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                            } else {
                                let value332: bool = (value169 == 6u32);
                                let value333: bool = (value332 && value250);
                                if value333 {
                                    let value334: u32 = ((input[83] as u32)).wrapping_add(1u32);
                                    let value335: u32 = (value233 ^ 0u32);
                                    let value336: u32 = core::cmp::min(value335, 1u32);
                                    let value337: u32 = (value336).wrapping_sub(1u32);
                                    let value338: u32 = (!value337);
                                    let value339: u32 = ((input[84] as u32) & value338);
                                    let value340: u32 = ((input[82] as u32) & value337);
                                    let value341: u32 = (value339 | value340);
                                    let value342: u32 = (value233 ^ 1u32);
                                    let value343: u32 = core::cmp::min(value342, 1u32);
                                    let value344: u32 = (value343).wrapping_sub(1u32);
                                    let value345: u32 = (!value344);
                                    let value346: u32 = ((input[85] as u32) & value345);
                                    let value347: u32 = ((input[82] as u32) & value344);
                                    let value348: u32 = (value346 | value347);
                                    let value349: u32 = (value233 ^ 2u32);
                                    let value350: u32 = core::cmp::min(value349, 1u32);
                                    let value351: u32 = (value350).wrapping_sub(1u32);
                                    let value352: u32 = (!value351);
                                    let value353: u32 = ((input[86] as u32) & value352);
                                    let value354: u32 = ((input[82] as u32) & value351);
                                    let value355: u32 = (value353 | value354);
                                    let value356: u32 = (value233 ^ 3u32);
                                    let value357: u32 = core::cmp::min(value356, 1u32);
                                    let value358: u32 = (value357).wrapping_sub(1u32);
                                    let value359: u32 = (!value358);
                                    let value360: u32 = ((input[87] as u32) & value359);
                                    let value361: u32 = ((input[82] as u32) & value358);
                                    let value362: u32 = (value360 | value361);
                                    let value363: u32 = (value233 ^ 4u32);
                                    let value364: u32 = core::cmp::min(value363, 1u32);
                                    let value365: u32 = (value364).wrapping_sub(1u32);
                                    let value366: u32 = (!value365);
                                    let value367: u32 = ((input[88] as u32) & value366);
                                    let value368: u32 = ((input[82] as u32) & value365);
                                    let value369: u32 = (value367 | value368);
                                    let value370: u32 = (value233 ^ 5u32);
                                    let value371: u32 = core::cmp::min(value370, 1u32);
                                    let value372: u32 = (value371).wrapping_sub(1u32);
                                    let value373: u32 = (!value372);
                                    let value374: u32 = ((input[89] as u32) & value373);
                                    let value375: u32 = ((input[82] as u32) & value372);
                                    let value376: u32 = (value374 | value375);
                                    let value377: u32 = (value233 ^ 6u32);
                                    let value378: u32 = core::cmp::min(value377, 1u32);
                                    let value379: u32 = (value378).wrapping_sub(1u32);
                                    let value380: u32 = (!value379);
                                    let value381: u32 = ((input[90] as u32) & value380);
                                    let value382: u32 = ((input[82] as u32) & value379);
                                    let value383: u32 = (value381 | value382);
                                    let value384: u32 = (value233 ^ 7u32);
                                    let value385: u32 = core::cmp::min(value384, 1u32);
                                    let value386: u32 = (value385).wrapping_sub(1u32);
                                    let value387: u32 = (!value386);
                                    let value388: u32 = ((input[91] as u32) & value387);
                                    let value389: u32 = ((input[82] as u32) & value386);
                                    let value390: u32 = (value388 | value389);
                                    let value391: u32 = (value233 ^ 8u32);
                                    let value392: u32 = core::cmp::min(value391, 1u32);
                                    let value393: u32 = (value392).wrapping_sub(1u32);
                                    let value394: u32 = (!value393);
                                    let value395: u32 = ((input[92] as u32) & value394);
                                    let value396: u32 = ((input[82] as u32) & value393);
                                    let value397: u32 = (value395 | value396);
                                    let value398: u32 = (value233 ^ 9u32);
                                    let value399: u32 = core::cmp::min(value398, 1u32);
                                    let value400: u32 = (value399).wrapping_sub(1u32);
                                    let value401: u32 = (!value400);
                                    let value402: u32 = ((input[93] as u32) & value401);
                                    let value403: u32 = ((input[82] as u32) & value400);
                                    let value404: u32 = (value402 | value403);
                                    let value405: u32 = (value233 ^ 10u32);
                                    let value406: u32 = core::cmp::min(value405, 1u32);
                                    let value407: u32 = (value406).wrapping_sub(1u32);
                                    let value408: u32 = (!value407);
                                    let value409: u32 = ((input[94] as u32) & value408);
                                    let value410: u32 = ((input[82] as u32) & value407);
                                    let value411: u32 = (value409 | value410);
                                    let value412: u32 = (value233 ^ 11u32);
                                    let value413: u32 = core::cmp::min(value412, 1u32);
                                    let value414: u32 = (value413).wrapping_sub(1u32);
                                    let value415: u32 = (!value414);
                                    let value416: u32 = ((input[95] as u32) & value415);
                                    let value417: u32 = ((input[82] as u32) & value414);
                                    let value418: u32 = (value416 | value417);
                                    let value419: u32 = (value233 ^ 12u32);
                                    let value420: u32 = core::cmp::min(value419, 1u32);
                                    let value421: u32 = (value420).wrapping_sub(1u32);
                                    let value422: u32 = (!value421);
                                    let value423: u32 = ((input[96] as u32) & value422);
                                    let value424: u32 = ((input[82] as u32) & value421);
                                    let value425: u32 = (value423 | value424);
                                    let value426: u32 = (value233 ^ 13u32);
                                    let value427: u32 = core::cmp::min(value426, 1u32);
                                    let value428: u32 = (value427).wrapping_sub(1u32);
                                    let value429: u32 = (!value428);
                                    let value430: u32 = ((input[97] as u32) & value429);
                                    let value431: u32 = ((input[82] as u32) & value428);
                                    let value432: u32 = (value430 | value431);
                                    let value433: u32 = (value233 ^ 14u32);
                                    let value434: u32 = core::cmp::min(value433, 1u32);
                                    let value435: u32 = (value434).wrapping_sub(1u32);
                                    let value436: u32 = (!value435);
                                    let value437: u32 = ((input[98] as u32) & value436);
                                    let value438: u32 = ((input[82] as u32) & value435);
                                    let value439: u32 = (value437 | value438);
                                    let value440: u32 = (value233 ^ 15u32);
                                    let value441: u32 = core::cmp::min(value440, 1u32);
                                    let value442: u32 = (value441).wrapping_sub(1u32);
                                    let value443: u32 = (!value442);
                                    let value444: u32 = ((input[99] as u32) & value443);
                                    let value445: u32 = ((input[82] as u32) & value442);
                                    let value446: u32 = (value444 | value445);
                                    [((input[82] as u32)), (value334), (value341), (value348), (value355), (value362), (value369), (value376), (value383), (value390), (value397), (value404), (value411), (value418), (value425), (value432), (value439), (value446), ((input[100] as u32)), (0u32), (0u32)]
                                } else {
                                    let value447: bool = (value169 == 7u32);
                                    let value448: bool = (value233 < (input[64] as u32));
                                    let value449: bool = (value447 && value448);
                                    if value449 {
                                        [((input[82] as u32)), (value233), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                                    } else {
                                        let value450: bool = (value169 == 8u32);
                                        let value451: bool = (value450 && value448);
                                        let value452: bool = ((input[82] as u32) == 0u32);
                                        let value453: bool = (value451 && value452);
                                        if value453 {
                                            [((input[82] as u32)), (value233), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                                        } else {
                                            let value454: bool = ((input[82] as u32) != 0u32);
                                            let value455: bool = (value451 && value454);
                                            if value455 {
                                                let value456: u32 = ((input[83] as u32)).wrapping_add(1u32);
                                                [((input[82] as u32)), (value456), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                                            } else {
                                                let value457: bool = (value169 == 9u32);
                                                let value458: bool = (value457 && value234);
                                                let value459: bool = ((input[100] as u32) < (input[81] as u32));
                                                let value460: bool = (value458 && value459);
                                                if value460 {
                                                    let value461: u32 = ((input[100] as u32) ^ 0u32);
                                                    let value462: u32 = core::cmp::min(value461, 1u32);
                                                    let value463: u32 = (value462).wrapping_sub(1u32);
                                                    let value464: u32 = ((input[65] as u32) & value463);
                                                    let value465: u32 = ((input[100] as u32) ^ 1u32);
                                                    let value466: u32 = core::cmp::min(value465, 1u32);
                                                    let value467: u32 = (value466).wrapping_sub(1u32);
                                                    let value468: u32 = ((input[66] as u32) & value467);
                                                    let value469: u32 = (value464 | value468);
                                                    let value470: u32 = ((input[100] as u32) ^ 2u32);
                                                    let value471: u32 = core::cmp::min(value470, 1u32);
                                                    let value472: u32 = (value471).wrapping_sub(1u32);
                                                    let value473: u32 = ((input[67] as u32) & value472);
                                                    let value474: u32 = (value469 | value473);
                                                    let value475: u32 = ((input[100] as u32) ^ 3u32);
                                                    let value476: u32 = core::cmp::min(value475, 1u32);
                                                    let value477: u32 = (value476).wrapping_sub(1u32);
                                                    let value478: u32 = ((input[68] as u32) & value477);
                                                    let value479: u32 = (value474 | value478);
                                                    let value480: u32 = ((input[100] as u32) ^ 4u32);
                                                    let value481: u32 = core::cmp::min(value480, 1u32);
                                                    let value482: u32 = (value481).wrapping_sub(1u32);
                                                    let value483: u32 = ((input[69] as u32) & value482);
                                                    let value484: u32 = (value479 | value483);
                                                    let value485: u32 = ((input[100] as u32) ^ 5u32);
                                                    let value486: u32 = core::cmp::min(value485, 1u32);
                                                    let value487: u32 = (value486).wrapping_sub(1u32);
                                                    let value488: u32 = ((input[70] as u32) & value487);
                                                    let value489: u32 = (value484 | value488);
                                                    let value490: u32 = ((input[100] as u32) ^ 6u32);
                                                    let value491: u32 = core::cmp::min(value490, 1u32);
                                                    let value492: u32 = (value491).wrapping_sub(1u32);
                                                    let value493: u32 = ((input[71] as u32) & value492);
                                                    let value494: u32 = (value489 | value493);
                                                    let value495: u32 = ((input[100] as u32) ^ 7u32);
                                                    let value496: u32 = core::cmp::min(value495, 1u32);
                                                    let value497: u32 = (value496).wrapping_sub(1u32);
                                                    let value498: u32 = ((input[72] as u32) & value497);
                                                    let value499: u32 = (value494 | value498);
                                                    let value500: u32 = ((input[100] as u32) ^ 8u32);
                                                    let value501: u32 = core::cmp::min(value500, 1u32);
                                                    let value502: u32 = (value501).wrapping_sub(1u32);
                                                    let value503: u32 = ((input[73] as u32) & value502);
                                                    let value504: u32 = (value499 | value503);
                                                    let value505: u32 = ((input[100] as u32) ^ 9u32);
                                                    let value506: u32 = core::cmp::min(value505, 1u32);
                                                    let value507: u32 = (value506).wrapping_sub(1u32);
                                                    let value508: u32 = ((input[74] as u32) & value507);
                                                    let value509: u32 = (value504 | value508);
                                                    let value510: u32 = ((input[100] as u32) ^ 10u32);
                                                    let value511: u32 = core::cmp::min(value510, 1u32);
                                                    let value512: u32 = (value511).wrapping_sub(1u32);
                                                    let value513: u32 = ((input[75] as u32) & value512);
                                                    let value514: u32 = (value509 | value513);
                                                    let value515: u32 = ((input[100] as u32) ^ 11u32);
                                                    let value516: u32 = core::cmp::min(value515, 1u32);
                                                    let value517: u32 = (value516).wrapping_sub(1u32);
                                                    let value518: u32 = ((input[76] as u32) & value517);
                                                    let value519: u32 = (value514 | value518);
                                                    let value520: u32 = ((input[100] as u32) ^ 12u32);
                                                    let value521: u32 = core::cmp::min(value520, 1u32);
                                                    let value522: u32 = (value521).wrapping_sub(1u32);
                                                    let value523: u32 = ((input[77] as u32) & value522);
                                                    let value524: u32 = (value519 | value523);
                                                    let value525: u32 = ((input[100] as u32) ^ 13u32);
                                                    let value526: u32 = core::cmp::min(value525, 1u32);
                                                    let value527: u32 = (value526).wrapping_sub(1u32);
                                                    let value528: u32 = ((input[78] as u32) & value527);
                                                    let value529: u32 = (value524 | value528);
                                                    let value530: u32 = ((input[100] as u32) ^ 14u32);
                                                    let value531: u32 = core::cmp::min(value530, 1u32);
                                                    let value532: u32 = (value531).wrapping_sub(1u32);
                                                    let value533: u32 = ((input[79] as u32) & value532);
                                                    let value534: u32 = (value529 | value533);
                                                    let value535: u32 = ((input[100] as u32) ^ 15u32);
                                                    let value536: u32 = core::cmp::min(value535, 1u32);
                                                    let value537: u32 = (value536).wrapping_sub(1u32);
                                                    let value538: u32 = ((input[80] as u32) & value537);
                                                    let value539: u32 = (value534 | value538);
                                                    let value540: u32 = ((input[83] as u32)).wrapping_add(1u32);
                                                    let value541: u32 = ((input[100] as u32)).wrapping_add(1u32);
                                                    [(value539), (value540), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), (value541), (0u32), (0u32)]
                                                } else {
                                                    let value542: bool = (value169 == 10u32);
                                                    let value543: bool = (value542 && value250);
                                                    if value543 {
                                                        let value544: u32 = (value233 ^ 0u32);
                                                        let value545: u32 = core::cmp::min(value544, 1u32);
                                                        let value546: u32 = (value545).wrapping_sub(1u32);
                                                        let value547: u32 = ((input[84] as u32) & value546);
                                                        let value548: u32 = (value233 ^ 1u32);
                                                        let value549: u32 = core::cmp::min(value548, 1u32);
                                                        let value550: u32 = (value549).wrapping_sub(1u32);
                                                        let value551: u32 = ((input[85] as u32) & value550);
                                                        let value552: u32 = (value547 | value551);
                                                        let value553: u32 = (value233 ^ 2u32);
                                                        let value554: u32 = core::cmp::min(value553, 1u32);
                                                        let value555: u32 = (value554).wrapping_sub(1u32);
                                                        let value556: u32 = ((input[86] as u32) & value555);
                                                        let value557: u32 = (value552 | value556);
                                                        let value558: u32 = (value233 ^ 3u32);
                                                        let value559: u32 = core::cmp::min(value558, 1u32);
                                                        let value560: u32 = (value559).wrapping_sub(1u32);
                                                        let value561: u32 = ((input[87] as u32) & value560);
                                                        let value562: u32 = (value557 | value561);
                                                        let value563: u32 = (value233 ^ 4u32);
                                                        let value564: u32 = core::cmp::min(value563, 1u32);
                                                        let value565: u32 = (value564).wrapping_sub(1u32);
                                                        let value566: u32 = ((input[88] as u32) & value565);
                                                        let value567: u32 = (value562 | value566);
                                                        let value568: u32 = (value233 ^ 5u32);
                                                        let value569: u32 = core::cmp::min(value568, 1u32);
                                                        let value570: u32 = (value569).wrapping_sub(1u32);
                                                        let value571: u32 = ((input[89] as u32) & value570);
                                                        let value572: u32 = (value567 | value571);
                                                        let value573: u32 = (value233 ^ 6u32);
                                                        let value574: u32 = core::cmp::min(value573, 1u32);
                                                        let value575: u32 = (value574).wrapping_sub(1u32);
                                                        let value576: u32 = ((input[90] as u32) & value575);
                                                        let value577: u32 = (value572 | value576);
                                                        let value578: u32 = (value233 ^ 7u32);
                                                        let value579: u32 = core::cmp::min(value578, 1u32);
                                                        let value580: u32 = (value579).wrapping_sub(1u32);
                                                        let value581: u32 = ((input[91] as u32) & value580);
                                                        let value582: u32 = (value577 | value581);
                                                        let value583: u32 = (value233 ^ 8u32);
                                                        let value584: u32 = core::cmp::min(value583, 1u32);
                                                        let value585: u32 = (value584).wrapping_sub(1u32);
                                                        let value586: u32 = ((input[92] as u32) & value585);
                                                        let value587: u32 = (value582 | value586);
                                                        let value588: u32 = (value233 ^ 9u32);
                                                        let value589: u32 = core::cmp::min(value588, 1u32);
                                                        let value590: u32 = (value589).wrapping_sub(1u32);
                                                        let value591: u32 = ((input[93] as u32) & value590);
                                                        let value592: u32 = (value587 | value591);
                                                        let value593: u32 = (value233 ^ 10u32);
                                                        let value594: u32 = core::cmp::min(value593, 1u32);
                                                        let value595: u32 = (value594).wrapping_sub(1u32);
                                                        let value596: u32 = ((input[94] as u32) & value595);
                                                        let value597: u32 = (value592 | value596);
                                                        let value598: u32 = (value233 ^ 11u32);
                                                        let value599: u32 = core::cmp::min(value598, 1u32);
                                                        let value600: u32 = (value599).wrapping_sub(1u32);
                                                        let value601: u32 = ((input[95] as u32) & value600);
                                                        let value602: u32 = (value597 | value601);
                                                        let value603: u32 = (value233 ^ 12u32);
                                                        let value604: u32 = core::cmp::min(value603, 1u32);
                                                        let value605: u32 = (value604).wrapping_sub(1u32);
                                                        let value606: u32 = ((input[96] as u32) & value605);
                                                        let value607: u32 = (value602 | value606);
                                                        let value608: u32 = (value233 ^ 13u32);
                                                        let value609: u32 = core::cmp::min(value608, 1u32);
                                                        let value610: u32 = (value609).wrapping_sub(1u32);
                                                        let value611: u32 = ((input[97] as u32) & value610);
                                                        let value612: u32 = (value607 | value611);
                                                        let value613: u32 = (value233 ^ 14u32);
                                                        let value614: u32 = core::cmp::min(value613, 1u32);
                                                        let value615: u32 = (value614).wrapping_sub(1u32);
                                                        let value616: u32 = ((input[98] as u32) & value615);
                                                        let value617: u32 = (value612 | value616);
                                                        let value618: u32 = (value233 ^ 15u32);
                                                        let value619: u32 = core::cmp::min(value618, 1u32);
                                                        let value620: u32 = (value619).wrapping_sub(1u32);
                                                        let value621: u32 = ((input[99] as u32) & value620);
                                                        let value622: u32 = (value617 | value621);
                                                        let value623: u32 = ((input[82] as u32)).wrapping_add(value622);
                                                        let value624: u32 = ((input[83] as u32)).wrapping_add(1u32);
                                                        [(value623), (value624), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                                                    } else {
                                                        let value625: bool = (value169 == 11u32);
                                                        let value626: bool = (value625 && value250);
                                                        if value626 {
                                                            let value627: u32 = (value233 ^ 0u32);
                                                            let value628: u32 = core::cmp::min(value627, 1u32);
                                                            let value629: u32 = (value628).wrapping_sub(1u32);
                                                            let value630: u32 = ((input[84] as u32) & value629);
                                                            let value631: u32 = (value233 ^ 1u32);
                                                            let value632: u32 = core::cmp::min(value631, 1u32);
                                                            let value633: u32 = (value632).wrapping_sub(1u32);
                                                            let value634: u32 = ((input[85] as u32) & value633);
                                                            let value635: u32 = (value630 | value634);
                                                            let value636: u32 = (value233 ^ 2u32);
                                                            let value637: u32 = core::cmp::min(value636, 1u32);
                                                            let value638: u32 = (value637).wrapping_sub(1u32);
                                                            let value639: u32 = ((input[86] as u32) & value638);
                                                            let value640: u32 = (value635 | value639);
                                                            let value641: u32 = (value233 ^ 3u32);
                                                            let value642: u32 = core::cmp::min(value641, 1u32);
                                                            let value643: u32 = (value642).wrapping_sub(1u32);
                                                            let value644: u32 = ((input[87] as u32) & value643);
                                                            let value645: u32 = (value640 | value644);
                                                            let value646: u32 = (value233 ^ 4u32);
                                                            let value647: u32 = core::cmp::min(value646, 1u32);
                                                            let value648: u32 = (value647).wrapping_sub(1u32);
                                                            let value649: u32 = ((input[88] as u32) & value648);
                                                            let value650: u32 = (value645 | value649);
                                                            let value651: u32 = (value233 ^ 5u32);
                                                            let value652: u32 = core::cmp::min(value651, 1u32);
                                                            let value653: u32 = (value652).wrapping_sub(1u32);
                                                            let value654: u32 = ((input[89] as u32) & value653);
                                                            let value655: u32 = (value650 | value654);
                                                            let value656: u32 = (value233 ^ 6u32);
                                                            let value657: u32 = core::cmp::min(value656, 1u32);
                                                            let value658: u32 = (value657).wrapping_sub(1u32);
                                                            let value659: u32 = ((input[90] as u32) & value658);
                                                            let value660: u32 = (value655 | value659);
                                                            let value661: u32 = (value233 ^ 7u32);
                                                            let value662: u32 = core::cmp::min(value661, 1u32);
                                                            let value663: u32 = (value662).wrapping_sub(1u32);
                                                            let value664: u32 = ((input[91] as u32) & value663);
                                                            let value665: u32 = (value660 | value664);
                                                            let value666: u32 = (value233 ^ 8u32);
                                                            let value667: u32 = core::cmp::min(value666, 1u32);
                                                            let value668: u32 = (value667).wrapping_sub(1u32);
                                                            let value669: u32 = ((input[92] as u32) & value668);
                                                            let value670: u32 = (value665 | value669);
                                                            let value671: u32 = (value233 ^ 9u32);
                                                            let value672: u32 = core::cmp::min(value671, 1u32);
                                                            let value673: u32 = (value672).wrapping_sub(1u32);
                                                            let value674: u32 = ((input[93] as u32) & value673);
                                                            let value675: u32 = (value670 | value674);
                                                            let value676: u32 = (value233 ^ 10u32);
                                                            let value677: u32 = core::cmp::min(value676, 1u32);
                                                            let value678: u32 = (value677).wrapping_sub(1u32);
                                                            let value679: u32 = ((input[94] as u32) & value678);
                                                            let value680: u32 = (value675 | value679);
                                                            let value681: u32 = (value233 ^ 11u32);
                                                            let value682: u32 = core::cmp::min(value681, 1u32);
                                                            let value683: u32 = (value682).wrapping_sub(1u32);
                                                            let value684: u32 = ((input[95] as u32) & value683);
                                                            let value685: u32 = (value680 | value684);
                                                            let value686: u32 = (value233 ^ 12u32);
                                                            let value687: u32 = core::cmp::min(value686, 1u32);
                                                            let value688: u32 = (value687).wrapping_sub(1u32);
                                                            let value689: u32 = ((input[96] as u32) & value688);
                                                            let value690: u32 = (value685 | value689);
                                                            let value691: u32 = (value233 ^ 13u32);
                                                            let value692: u32 = core::cmp::min(value691, 1u32);
                                                            let value693: u32 = (value692).wrapping_sub(1u32);
                                                            let value694: u32 = ((input[97] as u32) & value693);
                                                            let value695: u32 = (value690 | value694);
                                                            let value696: u32 = (value233 ^ 14u32);
                                                            let value697: u32 = core::cmp::min(value696, 1u32);
                                                            let value698: u32 = (value697).wrapping_sub(1u32);
                                                            let value699: u32 = ((input[98] as u32) & value698);
                                                            let value700: u32 = (value695 | value699);
                                                            let value701: u32 = (value233 ^ 15u32);
                                                            let value702: u32 = core::cmp::min(value701, 1u32);
                                                            let value703: u32 = (value702).wrapping_sub(1u32);
                                                            let value704: u32 = ((input[99] as u32) & value703);
                                                            let value705: u32 = (value700 | value704);
                                                            let value706: u32 = ((input[82] as u32)).wrapping_mul(value705);
                                                            let value707: u32 = ((input[83] as u32)).wrapping_add(1u32);
                                                            [(value706), (value707), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                                                        } else {
                                                            let value708: bool = (value169 == 12u32);
                                                            let value709: bool = (value708 && value250);
                                                            let value710: u32 = (value233 ^ 0u32);
                                                            let value711: u32 = core::cmp::min(value710, 1u32);
                                                            let value712: u32 = (value711).wrapping_sub(1u32);
                                                            let value713: u32 = ((input[84] as u32) & value712);
                                                            let value714: u32 = (value233 ^ 1u32);
                                                            let value715: u32 = core::cmp::min(value714, 1u32);
                                                            let value716: u32 = (value715).wrapping_sub(1u32);
                                                            let value717: u32 = ((input[85] as u32) & value716);
                                                            let value718: u32 = (value713 | value717);
                                                            let value719: u32 = (value233 ^ 2u32);
                                                            let value720: u32 = core::cmp::min(value719, 1u32);
                                                            let value721: u32 = (value720).wrapping_sub(1u32);
                                                            let value722: u32 = ((input[86] as u32) & value721);
                                                            let value723: u32 = (value718 | value722);
                                                            let value724: u32 = (value233 ^ 3u32);
                                                            let value725: u32 = core::cmp::min(value724, 1u32);
                                                            let value726: u32 = (value725).wrapping_sub(1u32);
                                                            let value727: u32 = ((input[87] as u32) & value726);
                                                            let value728: u32 = (value723 | value727);
                                                            let value729: u32 = (value233 ^ 4u32);
                                                            let value730: u32 = core::cmp::min(value729, 1u32);
                                                            let value731: u32 = (value730).wrapping_sub(1u32);
                                                            let value732: u32 = ((input[88] as u32) & value731);
                                                            let value733: u32 = (value728 | value732);
                                                            let value734: u32 = (value233 ^ 5u32);
                                                            let value735: u32 = core::cmp::min(value734, 1u32);
                                                            let value736: u32 = (value735).wrapping_sub(1u32);
                                                            let value737: u32 = ((input[89] as u32) & value736);
                                                            let value738: u32 = (value733 | value737);
                                                            let value739: u32 = (value233 ^ 6u32);
                                                            let value740: u32 = core::cmp::min(value739, 1u32);
                                                            let value741: u32 = (value740).wrapping_sub(1u32);
                                                            let value742: u32 = ((input[90] as u32) & value741);
                                                            let value743: u32 = (value738 | value742);
                                                            let value744: u32 = (value233 ^ 7u32);
                                                            let value745: u32 = core::cmp::min(value744, 1u32);
                                                            let value746: u32 = (value745).wrapping_sub(1u32);
                                                            let value747: u32 = ((input[91] as u32) & value746);
                                                            let value748: u32 = (value743 | value747);
                                                            let value749: u32 = (value233 ^ 8u32);
                                                            let value750: u32 = core::cmp::min(value749, 1u32);
                                                            let value751: u32 = (value750).wrapping_sub(1u32);
                                                            let value752: u32 = ((input[92] as u32) & value751);
                                                            let value753: u32 = (value748 | value752);
                                                            let value754: u32 = (value233 ^ 9u32);
                                                            let value755: u32 = core::cmp::min(value754, 1u32);
                                                            let value756: u32 = (value755).wrapping_sub(1u32);
                                                            let value757: u32 = ((input[93] as u32) & value756);
                                                            let value758: u32 = (value753 | value757);
                                                            let value759: u32 = (value233 ^ 10u32);
                                                            let value760: u32 = core::cmp::min(value759, 1u32);
                                                            let value761: u32 = (value760).wrapping_sub(1u32);
                                                            let value762: u32 = ((input[94] as u32) & value761);
                                                            let value763: u32 = (value758 | value762);
                                                            let value764: u32 = (value233 ^ 11u32);
                                                            let value765: u32 = core::cmp::min(value764, 1u32);
                                                            let value766: u32 = (value765).wrapping_sub(1u32);
                                                            let value767: u32 = ((input[95] as u32) & value766);
                                                            let value768: u32 = (value763 | value767);
                                                            let value769: u32 = (value233 ^ 12u32);
                                                            let value770: u32 = core::cmp::min(value769, 1u32);
                                                            let value771: u32 = (value770).wrapping_sub(1u32);
                                                            let value772: u32 = ((input[96] as u32) & value771);
                                                            let value773: u32 = (value768 | value772);
                                                            let value774: u32 = (value233 ^ 13u32);
                                                            let value775: u32 = core::cmp::min(value774, 1u32);
                                                            let value776: u32 = (value775).wrapping_sub(1u32);
                                                            let value777: u32 = ((input[97] as u32) & value776);
                                                            let value778: u32 = (value773 | value777);
                                                            let value779: u32 = (value233 ^ 14u32);
                                                            let value780: u32 = core::cmp::min(value779, 1u32);
                                                            let value781: u32 = (value780).wrapping_sub(1u32);
                                                            let value782: u32 = ((input[98] as u32) & value781);
                                                            let value783: u32 = (value778 | value782);
                                                            let value784: u32 = (value233 ^ 15u32);
                                                            let value785: u32 = core::cmp::min(value784, 1u32);
                                                            let value786: u32 = (value785).wrapping_sub(1u32);
                                                            let value787: u32 = ((input[99] as u32) & value786);
                                                            let value788: u32 = (value783 | value787);
                                                            let value789: bool = ((input[82] as u32) < value788);
                                                            let value790: bool = (value709 && value789);
                                                            if value790 {
                                                                let value791: u32 = ((input[83] as u32)).wrapping_add(1u32);
                                                                [(1u32), (value791), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                                                            } else {
                                                                let value792: bool = ((input[82] as u32) >= value788);
                                                                let value793: bool = (value709 && value792);
                                                                if value793 {
                                                                    let value794: u32 = ((input[83] as u32)).wrapping_add(1u32);
                                                                    [(0u32), (value794), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                                                                } else {
                                                                    let value795: bool = (value169 == 13u32);
                                                                    let value796: bool = (value795 && value250);
                                                                    if value796 {
                                                                        let value797: u32 = core::cmp::max((input[82] as u32), value788);
                                                                        let value798: u32 = ((input[83] as u32)).wrapping_add(1u32);
                                                                        [(value797), (value798), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                                                                    } else {
                                                                        let value799: bool = (value169 == 14u32);
                                                                        let value800: bool = (value799 && value250);
                                                                        if value800 {
                                                                            let value801: u32 = core::cmp::min((input[82] as u32), value788);
                                                                            let value802: u32 = ((input[83] as u32)).wrapping_add(1u32);
                                                                            [(value801), (value802), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                                                                        } else {
                                                                            let value803: bool = (value169 == 15u32);
                                                                            let value804: bool = (value803 && value234);
                                                                            let value805: bool = (value804 && value454);
                                                                            if value805 {
                                                                                let value806: u32 = ((input[83] as u32)).wrapping_add(1u32);
                                                                                [((input[82] as u32)), (value806), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                                                                            } else {
                                                                                let value807: bool = (value169 == 16u32);
                                                                                let value808: bool = (value807 && value234);
                                                                                if value808 {
                                                                                    let value809: u32 = ((input[83] as u32)).wrapping_add(1u32);
                                                                                    [((input[82] as u32)), (value809), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                                                                                } else {
                                                                                    let value810: bool = (value169 == 17u32);
                                                                                    if value810 {
                                                                                        let value811: bool = ((input[82] as u32) < value233);
                                                                                        if value811 {
                                                                                            let value812: u32 = ((input[83] as u32)).wrapping_add(1u32);
                                                                                            [(1u32), (value812), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                                                                                        } else {
                                                                                            let value813: u32 = ((input[83] as u32)).wrapping_add(1u32);
                                                                                            [(0u32), (value813), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), (0u32), (0u32)]
                                                                                        }
                                                                                    } else {
                                                                                        [((input[82] as u32)), ((input[83] as u32)), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), ((input[101] as u32)), (1u32)]
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    } else {
        [((input[82] as u32)), ((input[83] as u32)), ((input[84] as u32)), ((input[85] as u32)), ((input[86] as u32)), ((input[87] as u32)), ((input[88] as u32)), ((input[89] as u32)), ((input[90] as u32)), ((input[91] as u32)), ((input[92] as u32)), ((input[93] as u32)), ((input[94] as u32)), ((input[95] as u32)), ((input[96] as u32)), ((input[97] as u32)), ((input[98] as u32)), ((input[99] as u32)), ((input[100] as u32)), ((input[101] as u32)), (1u32)]
    }
}

pub fn tau_step(input:&[u128;102])->[u128;21] {
    let words = core::array::from_fn(|i| input[i] as u32);
    tau_step32(&words).map(u128::from)
}
