import Proofs
open SupportCells
set_option maxRecDepth 10000
set_option maxHeartbeats 0

-- Lean index 0 is the newest slot; Python slot 0 is the oldest slot.
def pythonCell {n : Nat} (v : Val n) : Nat :=
  (List.finRange n).foldl (fun a i => a + (v i).toNat * 2 ^ (n - 1 - i.val)) 0

def fromMask {n : Nat} (mask : Nat) : Val n → Bool :=
  fun v => mask.testBit (pythonCell v)

def asMask {n : Nat} (s : Val n → Bool) : Nat :=
  (allVal n).foldl (fun mask v => if s v then mask + 2 ^ pythonCell v else mask) 0

def resultLine {n : Nat} (id : String) (f : Formula n) : IO Unit :=
  IO.println (id ++ ":" ++ String.join
    ((List.range (2 ^ (2 ^ n) - 1)).map fun k => if f.eval (fromMask (k + 1)) then "1" else "0"))

def refinementLine (n mask : Nat) : IO Unit :=
  IO.println ("r" ++ toString n ++ ":" ++ toString mask ++ ":" ++ String.intercalate ","
    (((allSupport (n + 1)).filter (refinesB (fromMask mask))).map (fun s => toString (asMask s))))

def f0000 : Formula 0 := (.eq .zero .zero)
def f0001 : Formula 0 := (.neg (.eq .zero .zero))
def f0002 : Formula 0 := (.eq .one .zero)
def f0003 : Formula 0 := (.neg (.eq .one .zero))
def f0004 : Formula 0 := (.eq (.neg .zero) .zero)
def f0005 : Formula 0 := (.neg (.eq (.neg .zero) .zero))
def f0006 : Formula 0 := (.eq (.neg .one) .zero)
def f0007 : Formula 0 := (.neg (.eq (.neg .one) .zero))
def f0008 : Formula 0 := (.eq (.meet .zero .zero) .zero)
def f0009 : Formula 0 := (.neg (.eq (.meet .zero .zero) .zero))
def f0010 : Formula 0 := (.eq (.meet .zero .one) .zero)
def f0011 : Formula 0 := (.neg (.eq (.meet .zero .one) .zero))
def f0012 : Formula 0 := (.eq (.meet .one .zero) .zero)
def f0013 : Formula 0 := (.neg (.eq (.meet .one .zero) .zero))
def f0014 : Formula 0 := (.eq (.meet .one .one) .zero)
def f0015 : Formula 0 := (.neg (.eq (.meet .one .one) .zero))
def f0016 : Formula 0 := (.eq (.join .zero .zero) .zero)
def f0017 : Formula 0 := (.neg (.eq (.join .zero .zero) .zero))
def f0018 : Formula 0 := (.eq (.join .zero .one) .zero)
def f0019 : Formula 0 := (.neg (.eq (.join .zero .one) .zero))
def f0020 : Formula 0 := (.eq (.join .one .zero) .zero)
def f0021 : Formula 0 := (.neg (.eq (.join .one .zero) .zero))
def f0022 : Formula 0 := (.eq (.join .one .one) .zero)
def f0023 : Formula 0 := (.neg (.eq (.join .one .one) .zero))
def f0024 : Formula 0 := (.eq (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero)) .zero)
def f0025 : Formula 0 := (.neg (.eq (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero)) .zero))
def f0026 : Formula 0 := (.eq (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one)) .zero)
def f0027 : Formula 0 := (.neg (.eq (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one)) .zero))
def f0028 : Formula 0 := (.eq (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero)) .zero)
def f0029 : Formula 0 := (.neg (.eq (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero)) .zero))
def f0030 : Formula 0 := (.eq (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one)) .zero)
def f0031 : Formula 0 := (.neg (.eq (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one)) .zero))
def f0032 : Formula 0 := (.neg (.eq .zero .zero))
def f0033 : Formula 0 := (.conj (.eq .zero .zero) (.eq .zero .zero))
def f0034 : Formula 0 := (.disj (.eq .zero .zero) (.eq .zero .zero))
def f0035 : Formula 0 := (.conj (.eq .zero .zero) (.eq .one .zero))
def f0036 : Formula 0 := (.disj (.eq .zero .zero) (.eq .one .zero))
def f0037 : Formula 0 := (.neg (.eq .one .zero))
def f0038 : Formula 0 := (.conj (.eq .one .zero) (.eq .zero .zero))
def f0039 : Formula 0 := (.disj (.eq .one .zero) (.eq .zero .zero))
def f0040 : Formula 0 := (.conj (.eq .one .zero) (.eq .one .zero))
def f0041 : Formula 0 := (.disj (.eq .one .zero) (.eq .one .zero))
def f0042 : Formula 0 := (.ex (.eq .zero .zero))
def f0043 : Formula 0 := (.ex (.neg (.eq .zero .zero)))
def f0044 : Formula 0 := (.ex (.eq .one .zero))
def f0045 : Formula 0 := (.ex (.neg (.eq .one .zero)))
def f0046 : Formula 0 := (.ex (.eq (.var 0) .zero))
def f0047 : Formula 0 := (.ex (.neg (.eq (.var 0) .zero)))
def f0048 : Formula 0 := (.ex (.eq (.neg .zero) .zero))
def f0049 : Formula 0 := (.ex (.neg (.eq (.neg .zero) .zero)))
def f0050 : Formula 0 := (.ex (.eq (.neg .one) .zero))
def f0051 : Formula 0 := (.ex (.neg (.eq (.neg .one) .zero)))
def f0052 : Formula 0 := (.ex (.eq (.neg (.var 0)) .zero))
def f0053 : Formula 0 := (.ex (.neg (.eq (.neg (.var 0)) .zero)))
def f0054 : Formula 0 := (.ex (.eq (.meet .zero .zero) .zero))
def f0055 : Formula 0 := (.ex (.neg (.eq (.meet .zero .zero) .zero)))
def f0056 : Formula 0 := (.ex (.eq (.meet .zero .one) .zero))
def f0057 : Formula 0 := (.ex (.neg (.eq (.meet .zero .one) .zero)))
def f0058 : Formula 0 := (.ex (.eq (.meet .zero (.var 0)) .zero))
def f0059 : Formula 0 := (.ex (.neg (.eq (.meet .zero (.var 0)) .zero)))
def f0060 : Formula 0 := (.ex (.eq (.meet .one .zero) .zero))
def f0061 : Formula 0 := (.ex (.neg (.eq (.meet .one .zero) .zero)))
def f0062 : Formula 0 := (.ex (.eq (.meet .one .one) .zero))
def f0063 : Formula 0 := (.ex (.neg (.eq (.meet .one .one) .zero)))
def f0064 : Formula 0 := (.ex (.eq (.meet .one (.var 0)) .zero))
def f0065 : Formula 0 := (.ex (.neg (.eq (.meet .one (.var 0)) .zero)))
def f0066 : Formula 0 := (.ex (.eq (.meet (.var 0) .zero) .zero))
def f0067 : Formula 0 := (.ex (.neg (.eq (.meet (.var 0) .zero) .zero)))
def f0068 : Formula 0 := (.ex (.eq (.meet (.var 0) .one) .zero))
def f0069 : Formula 0 := (.ex (.neg (.eq (.meet (.var 0) .one) .zero)))
def f0070 : Formula 0 := (.ex (.eq (.meet (.var 0) (.var 0)) .zero))
def f0071 : Formula 0 := (.ex (.neg (.eq (.meet (.var 0) (.var 0)) .zero)))
def f0072 : Formula 0 := (.ex (.eq (.join .zero .zero) .zero))
def f0073 : Formula 0 := (.ex (.neg (.eq (.join .zero .zero) .zero)))
def f0074 : Formula 0 := (.ex (.eq (.join .zero .one) .zero))
def f0075 : Formula 0 := (.ex (.neg (.eq (.join .zero .one) .zero)))
def f0076 : Formula 0 := (.ex (.eq (.join .zero (.var 0)) .zero))
def f0077 : Formula 0 := (.ex (.neg (.eq (.join .zero (.var 0)) .zero)))
def f0078 : Formula 0 := (.ex (.eq (.join .one .zero) .zero))
def f0079 : Formula 0 := (.ex (.neg (.eq (.join .one .zero) .zero)))
def f0080 : Formula 0 := (.ex (.eq (.join .one .one) .zero))
def f0081 : Formula 0 := (.ex (.neg (.eq (.join .one .one) .zero)))
def f0082 : Formula 0 := (.ex (.eq (.join .one (.var 0)) .zero))
def f0083 : Formula 0 := (.ex (.neg (.eq (.join .one (.var 0)) .zero)))
def f0084 : Formula 0 := (.ex (.eq (.join (.var 0) .zero) .zero))
def f0085 : Formula 0 := (.ex (.neg (.eq (.join (.var 0) .zero) .zero)))
def f0086 : Formula 0 := (.ex (.eq (.join (.var 0) .one) .zero))
def f0087 : Formula 0 := (.ex (.neg (.eq (.join (.var 0) .one) .zero)))
def f0088 : Formula 0 := (.ex (.eq (.join (.var 0) (.var 0)) .zero))
def f0089 : Formula 0 := (.ex (.neg (.eq (.join (.var 0) (.var 0)) .zero)))
def f0090 : Formula 0 := (.ex (.eq (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero)) .zero))
def f0091 : Formula 0 := (.ex (.neg (.eq (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero)) .zero)))
def f0092 : Formula 0 := (.ex (.eq (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one)) .zero))
def f0093 : Formula 0 := (.ex (.neg (.eq (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one)) .zero)))
def f0094 : Formula 0 := (.ex (.eq (.join (.meet .zero (.neg (.var 0))) (.meet (.neg .zero) (.var 0))) .zero))
def f0095 : Formula 0 := (.ex (.neg (.eq (.join (.meet .zero (.neg (.var 0))) (.meet (.neg .zero) (.var 0))) .zero)))
def f0096 : Formula 0 := (.ex (.eq (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero)) .zero))
def f0097 : Formula 0 := (.ex (.neg (.eq (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero)) .zero)))
def f0098 : Formula 0 := (.ex (.eq (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one)) .zero))
def f0099 : Formula 0 := (.ex (.neg (.eq (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one)) .zero)))
def f0100 : Formula 0 := (.ex (.eq (.join (.meet .one (.neg (.var 0))) (.meet (.neg .one) (.var 0))) .zero))
def f0101 : Formula 0 := (.ex (.neg (.eq (.join (.meet .one (.neg (.var 0))) (.meet (.neg .one) (.var 0))) .zero)))
def f0102 : Formula 0 := (.ex (.eq (.join (.meet (.var 0) (.neg .zero)) (.meet (.neg (.var 0)) .zero)) .zero))
def f0103 : Formula 0 := (.ex (.neg (.eq (.join (.meet (.var 0) (.neg .zero)) (.meet (.neg (.var 0)) .zero)) .zero)))
def f0104 : Formula 0 := (.ex (.eq (.join (.meet (.var 0) (.neg .one)) (.meet (.neg (.var 0)) .one)) .zero))
def f0105 : Formula 0 := (.ex (.neg (.eq (.join (.meet (.var 0) (.neg .one)) (.meet (.neg (.var 0)) .one)) .zero)))
def f0106 : Formula 0 := (.ex (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero))
def f0107 : Formula 0 := (.ex (.neg (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero)))
def f0108 : Formula 0 := (.ex (.conj (.neg (.eq (.meet (.var 0) .zero) .zero)) (.neg (.eq (.meet (.neg (.var 0)) .zero) .zero))))
def f0109 : Formula 0 := (.ex (.conj (.neg (.eq (.meet (.var 0) .one) .zero)) (.neg (.eq (.meet (.neg (.var 0)) .one) .zero))))
def f0110 : Formula 0 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.neg .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.neg .zero)) .zero))))
def f0111 : Formula 0 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.neg .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.neg .one)) .zero))))
def f0112 : Formula 0 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .zero .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .zero .zero)) .zero))))
def f0113 : Formula 0 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .zero .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .zero .one)) .zero))))
def f0114 : Formula 0 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .one .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .one .zero)) .zero))))
def f0115 : Formula 0 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .one .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .one .one)) .zero))))
def f0116 : Formula 0 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .zero .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .zero .zero)) .zero))))
def f0117 : Formula 0 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .zero .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .zero .one)) .zero))))
def f0118 : Formula 0 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .one .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .one .zero)) .zero))))
def f0119 : Formula 0 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .one .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .one .one)) .zero))))
def f0120 : Formula 0 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero))) .zero))))
def f0121 : Formula 0 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one))) .zero))))
def f0122 : Formula 0 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero))) .zero))))
def f0123 : Formula 0 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one))) .zero))))
def f0124 : Formula 1 := (.eq .zero .zero)
def f0125 : Formula 1 := (.neg (.eq .zero .zero))
def f0126 : Formula 1 := (.eq .one .zero)
def f0127 : Formula 1 := (.neg (.eq .one .zero))
def f0128 : Formula 1 := (.eq (.var 0) .zero)
def f0129 : Formula 1 := (.neg (.eq (.var 0) .zero))
def f0130 : Formula 1 := (.eq (.neg .zero) .zero)
def f0131 : Formula 1 := (.neg (.eq (.neg .zero) .zero))
def f0132 : Formula 1 := (.eq (.neg .one) .zero)
def f0133 : Formula 1 := (.neg (.eq (.neg .one) .zero))
def f0134 : Formula 1 := (.eq (.neg (.var 0)) .zero)
def f0135 : Formula 1 := (.neg (.eq (.neg (.var 0)) .zero))
def f0136 : Formula 1 := (.eq (.meet .zero .zero) .zero)
def f0137 : Formula 1 := (.neg (.eq (.meet .zero .zero) .zero))
def f0138 : Formula 1 := (.eq (.meet .zero .one) .zero)
def f0139 : Formula 1 := (.neg (.eq (.meet .zero .one) .zero))
def f0140 : Formula 1 := (.eq (.meet .zero (.var 0)) .zero)
def f0141 : Formula 1 := (.neg (.eq (.meet .zero (.var 0)) .zero))
def f0142 : Formula 1 := (.eq (.meet .one .zero) .zero)
def f0143 : Formula 1 := (.neg (.eq (.meet .one .zero) .zero))
def f0144 : Formula 1 := (.eq (.meet .one .one) .zero)
def f0145 : Formula 1 := (.neg (.eq (.meet .one .one) .zero))
def f0146 : Formula 1 := (.eq (.meet .one (.var 0)) .zero)
def f0147 : Formula 1 := (.neg (.eq (.meet .one (.var 0)) .zero))
def f0148 : Formula 1 := (.eq (.meet (.var 0) .zero) .zero)
def f0149 : Formula 1 := (.neg (.eq (.meet (.var 0) .zero) .zero))
def f0150 : Formula 1 := (.eq (.meet (.var 0) .one) .zero)
def f0151 : Formula 1 := (.neg (.eq (.meet (.var 0) .one) .zero))
def f0152 : Formula 1 := (.eq (.meet (.var 0) (.var 0)) .zero)
def f0153 : Formula 1 := (.neg (.eq (.meet (.var 0) (.var 0)) .zero))
def f0154 : Formula 1 := (.eq (.join .zero .zero) .zero)
def f0155 : Formula 1 := (.neg (.eq (.join .zero .zero) .zero))
def f0156 : Formula 1 := (.eq (.join .zero .one) .zero)
def f0157 : Formula 1 := (.neg (.eq (.join .zero .one) .zero))
def f0158 : Formula 1 := (.eq (.join .zero (.var 0)) .zero)
def f0159 : Formula 1 := (.neg (.eq (.join .zero (.var 0)) .zero))
def f0160 : Formula 1 := (.eq (.join .one .zero) .zero)
def f0161 : Formula 1 := (.neg (.eq (.join .one .zero) .zero))
def f0162 : Formula 1 := (.eq (.join .one .one) .zero)
def f0163 : Formula 1 := (.neg (.eq (.join .one .one) .zero))
def f0164 : Formula 1 := (.eq (.join .one (.var 0)) .zero)
def f0165 : Formula 1 := (.neg (.eq (.join .one (.var 0)) .zero))
def f0166 : Formula 1 := (.eq (.join (.var 0) .zero) .zero)
def f0167 : Formula 1 := (.neg (.eq (.join (.var 0) .zero) .zero))
def f0168 : Formula 1 := (.eq (.join (.var 0) .one) .zero)
def f0169 : Formula 1 := (.neg (.eq (.join (.var 0) .one) .zero))
def f0170 : Formula 1 := (.eq (.join (.var 0) (.var 0)) .zero)
def f0171 : Formula 1 := (.neg (.eq (.join (.var 0) (.var 0)) .zero))
def f0172 : Formula 1 := (.eq (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero)) .zero)
def f0173 : Formula 1 := (.neg (.eq (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero)) .zero))
def f0174 : Formula 1 := (.eq (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one)) .zero)
def f0175 : Formula 1 := (.neg (.eq (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one)) .zero))
def f0176 : Formula 1 := (.eq (.join (.meet .zero (.neg (.var 0))) (.meet (.neg .zero) (.var 0))) .zero)
def f0177 : Formula 1 := (.neg (.eq (.join (.meet .zero (.neg (.var 0))) (.meet (.neg .zero) (.var 0))) .zero))
def f0178 : Formula 1 := (.eq (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero)) .zero)
def f0179 : Formula 1 := (.neg (.eq (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero)) .zero))
def f0180 : Formula 1 := (.eq (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one)) .zero)
def f0181 : Formula 1 := (.neg (.eq (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one)) .zero))
def f0182 : Formula 1 := (.eq (.join (.meet .one (.neg (.var 0))) (.meet (.neg .one) (.var 0))) .zero)
def f0183 : Formula 1 := (.neg (.eq (.join (.meet .one (.neg (.var 0))) (.meet (.neg .one) (.var 0))) .zero))
def f0184 : Formula 1 := (.eq (.join (.meet (.var 0) (.neg .zero)) (.meet (.neg (.var 0)) .zero)) .zero)
def f0185 : Formula 1 := (.neg (.eq (.join (.meet (.var 0) (.neg .zero)) (.meet (.neg (.var 0)) .zero)) .zero))
def f0186 : Formula 1 := (.eq (.join (.meet (.var 0) (.neg .one)) (.meet (.neg (.var 0)) .one)) .zero)
def f0187 : Formula 1 := (.neg (.eq (.join (.meet (.var 0) (.neg .one)) (.meet (.neg (.var 0)) .one)) .zero))
def f0188 : Formula 1 := (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero)
def f0189 : Formula 1 := (.neg (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero))
def f0190 : Formula 1 := (.neg (.eq .zero .zero))
def f0191 : Formula 1 := (.conj (.eq .zero .zero) (.eq .zero .zero))
def f0192 : Formula 1 := (.disj (.eq .zero .zero) (.eq .zero .zero))
def f0193 : Formula 1 := (.conj (.eq .zero .zero) (.eq .one .zero))
def f0194 : Formula 1 := (.disj (.eq .zero .zero) (.eq .one .zero))
def f0195 : Formula 1 := (.conj (.eq .zero .zero) (.eq (.var 0) .zero))
def f0196 : Formula 1 := (.disj (.eq .zero .zero) (.eq (.var 0) .zero))
def f0197 : Formula 1 := (.neg (.eq .one .zero))
def f0198 : Formula 1 := (.conj (.eq .one .zero) (.eq .zero .zero))
def f0199 : Formula 1 := (.disj (.eq .one .zero) (.eq .zero .zero))
def f0200 : Formula 1 := (.conj (.eq .one .zero) (.eq .one .zero))
def f0201 : Formula 1 := (.disj (.eq .one .zero) (.eq .one .zero))
def f0202 : Formula 1 := (.conj (.eq .one .zero) (.eq (.var 0) .zero))
def f0203 : Formula 1 := (.disj (.eq .one .zero) (.eq (.var 0) .zero))
def f0204 : Formula 1 := (.neg (.eq (.var 0) .zero))
def f0205 : Formula 1 := (.conj (.eq (.var 0) .zero) (.eq .zero .zero))
def f0206 : Formula 1 := (.disj (.eq (.var 0) .zero) (.eq .zero .zero))
def f0207 : Formula 1 := (.conj (.eq (.var 0) .zero) (.eq .one .zero))
def f0208 : Formula 1 := (.disj (.eq (.var 0) .zero) (.eq .one .zero))
def f0209 : Formula 1 := (.conj (.eq (.var 0) .zero) (.eq (.var 0) .zero))
def f0210 : Formula 1 := (.disj (.eq (.var 0) .zero) (.eq (.var 0) .zero))
def f0211 : Formula 1 := (.ex (.eq .zero .zero))
def f0212 : Formula 1 := (.ex (.neg (.eq .zero .zero)))
def f0213 : Formula 1 := (.ex (.eq .one .zero))
def f0214 : Formula 1 := (.ex (.neg (.eq .one .zero)))
def f0215 : Formula 1 := (.ex (.eq (.var 1) .zero))
def f0216 : Formula 1 := (.ex (.neg (.eq (.var 1) .zero)))
def f0217 : Formula 1 := (.ex (.eq (.var 0) .zero))
def f0218 : Formula 1 := (.ex (.neg (.eq (.var 0) .zero)))
def f0219 : Formula 1 := (.ex (.eq (.neg .zero) .zero))
def f0220 : Formula 1 := (.ex (.neg (.eq (.neg .zero) .zero)))
def f0221 : Formula 1 := (.ex (.eq (.neg .one) .zero))
def f0222 : Formula 1 := (.ex (.neg (.eq (.neg .one) .zero)))
def f0223 : Formula 1 := (.ex (.eq (.neg (.var 1)) .zero))
def f0224 : Formula 1 := (.ex (.neg (.eq (.neg (.var 1)) .zero)))
def f0225 : Formula 1 := (.ex (.eq (.neg (.var 0)) .zero))
def f0226 : Formula 1 := (.ex (.neg (.eq (.neg (.var 0)) .zero)))
def f0227 : Formula 1 := (.ex (.eq (.meet .zero .zero) .zero))
def f0228 : Formula 1 := (.ex (.neg (.eq (.meet .zero .zero) .zero)))
def f0229 : Formula 1 := (.ex (.eq (.meet .zero .one) .zero))
def f0230 : Formula 1 := (.ex (.neg (.eq (.meet .zero .one) .zero)))
def f0231 : Formula 1 := (.ex (.eq (.meet .zero (.var 1)) .zero))
def f0232 : Formula 1 := (.ex (.neg (.eq (.meet .zero (.var 1)) .zero)))
def f0233 : Formula 1 := (.ex (.eq (.meet .zero (.var 0)) .zero))
def f0234 : Formula 1 := (.ex (.neg (.eq (.meet .zero (.var 0)) .zero)))
def f0235 : Formula 1 := (.ex (.eq (.meet .one .zero) .zero))
def f0236 : Formula 1 := (.ex (.neg (.eq (.meet .one .zero) .zero)))
def f0237 : Formula 1 := (.ex (.eq (.meet .one .one) .zero))
def f0238 : Formula 1 := (.ex (.neg (.eq (.meet .one .one) .zero)))
def f0239 : Formula 1 := (.ex (.eq (.meet .one (.var 1)) .zero))
def f0240 : Formula 1 := (.ex (.neg (.eq (.meet .one (.var 1)) .zero)))
def f0241 : Formula 1 := (.ex (.eq (.meet .one (.var 0)) .zero))
def f0242 : Formula 1 := (.ex (.neg (.eq (.meet .one (.var 0)) .zero)))
def f0243 : Formula 1 := (.ex (.eq (.meet (.var 1) .zero) .zero))
def f0244 : Formula 1 := (.ex (.neg (.eq (.meet (.var 1) .zero) .zero)))
def f0245 : Formula 1 := (.ex (.eq (.meet (.var 1) .one) .zero))
def f0246 : Formula 1 := (.ex (.neg (.eq (.meet (.var 1) .one) .zero)))
def f0247 : Formula 1 := (.ex (.eq (.meet (.var 1) (.var 1)) .zero))
def f0248 : Formula 1 := (.ex (.neg (.eq (.meet (.var 1) (.var 1)) .zero)))
def f0249 : Formula 1 := (.ex (.eq (.meet (.var 1) (.var 0)) .zero))
def f0250 : Formula 1 := (.ex (.neg (.eq (.meet (.var 1) (.var 0)) .zero)))
def f0251 : Formula 1 := (.ex (.eq (.meet (.var 0) .zero) .zero))
def f0252 : Formula 1 := (.ex (.neg (.eq (.meet (.var 0) .zero) .zero)))
def f0253 : Formula 1 := (.ex (.eq (.meet (.var 0) .one) .zero))
def f0254 : Formula 1 := (.ex (.neg (.eq (.meet (.var 0) .one) .zero)))
def f0255 : Formula 1 := (.ex (.eq (.meet (.var 0) (.var 1)) .zero))
def f0256 : Formula 1 := (.ex (.neg (.eq (.meet (.var 0) (.var 1)) .zero)))
def f0257 : Formula 1 := (.ex (.eq (.meet (.var 0) (.var 0)) .zero))
def f0258 : Formula 1 := (.ex (.neg (.eq (.meet (.var 0) (.var 0)) .zero)))
def f0259 : Formula 1 := (.ex (.eq (.join .zero .zero) .zero))
def f0260 : Formula 1 := (.ex (.neg (.eq (.join .zero .zero) .zero)))
def f0261 : Formula 1 := (.ex (.eq (.join .zero .one) .zero))
def f0262 : Formula 1 := (.ex (.neg (.eq (.join .zero .one) .zero)))
def f0263 : Formula 1 := (.ex (.eq (.join .zero (.var 1)) .zero))
def f0264 : Formula 1 := (.ex (.neg (.eq (.join .zero (.var 1)) .zero)))
def f0265 : Formula 1 := (.ex (.eq (.join .zero (.var 0)) .zero))
def f0266 : Formula 1 := (.ex (.neg (.eq (.join .zero (.var 0)) .zero)))
def f0267 : Formula 1 := (.ex (.eq (.join .one .zero) .zero))
def f0268 : Formula 1 := (.ex (.neg (.eq (.join .one .zero) .zero)))
def f0269 : Formula 1 := (.ex (.eq (.join .one .one) .zero))
def f0270 : Formula 1 := (.ex (.neg (.eq (.join .one .one) .zero)))
def f0271 : Formula 1 := (.ex (.eq (.join .one (.var 1)) .zero))
def f0272 : Formula 1 := (.ex (.neg (.eq (.join .one (.var 1)) .zero)))
def f0273 : Formula 1 := (.ex (.eq (.join .one (.var 0)) .zero))
def f0274 : Formula 1 := (.ex (.neg (.eq (.join .one (.var 0)) .zero)))
def f0275 : Formula 1 := (.ex (.eq (.join (.var 1) .zero) .zero))
def f0276 : Formula 1 := (.ex (.neg (.eq (.join (.var 1) .zero) .zero)))
def f0277 : Formula 1 := (.ex (.eq (.join (.var 1) .one) .zero))
def f0278 : Formula 1 := (.ex (.neg (.eq (.join (.var 1) .one) .zero)))
def f0279 : Formula 1 := (.ex (.eq (.join (.var 1) (.var 1)) .zero))
def f0280 : Formula 1 := (.ex (.neg (.eq (.join (.var 1) (.var 1)) .zero)))
def f0281 : Formula 1 := (.ex (.eq (.join (.var 1) (.var 0)) .zero))
def f0282 : Formula 1 := (.ex (.neg (.eq (.join (.var 1) (.var 0)) .zero)))
def f0283 : Formula 1 := (.ex (.eq (.join (.var 0) .zero) .zero))
def f0284 : Formula 1 := (.ex (.neg (.eq (.join (.var 0) .zero) .zero)))
def f0285 : Formula 1 := (.ex (.eq (.join (.var 0) .one) .zero))
def f0286 : Formula 1 := (.ex (.neg (.eq (.join (.var 0) .one) .zero)))
def f0287 : Formula 1 := (.ex (.eq (.join (.var 0) (.var 1)) .zero))
def f0288 : Formula 1 := (.ex (.neg (.eq (.join (.var 0) (.var 1)) .zero)))
def f0289 : Formula 1 := (.ex (.eq (.join (.var 0) (.var 0)) .zero))
def f0290 : Formula 1 := (.ex (.neg (.eq (.join (.var 0) (.var 0)) .zero)))
def f0291 : Formula 1 := (.ex (.eq (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero)) .zero))
def f0292 : Formula 1 := (.ex (.neg (.eq (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero)) .zero)))
def f0293 : Formula 1 := (.ex (.eq (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one)) .zero))
def f0294 : Formula 1 := (.ex (.neg (.eq (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one)) .zero)))
def f0295 : Formula 1 := (.ex (.eq (.join (.meet .zero (.neg (.var 1))) (.meet (.neg .zero) (.var 1))) .zero))
def f0296 : Formula 1 := (.ex (.neg (.eq (.join (.meet .zero (.neg (.var 1))) (.meet (.neg .zero) (.var 1))) .zero)))
def f0297 : Formula 1 := (.ex (.eq (.join (.meet .zero (.neg (.var 0))) (.meet (.neg .zero) (.var 0))) .zero))
def f0298 : Formula 1 := (.ex (.neg (.eq (.join (.meet .zero (.neg (.var 0))) (.meet (.neg .zero) (.var 0))) .zero)))
def f0299 : Formula 1 := (.ex (.eq (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero)) .zero))
def f0300 : Formula 1 := (.ex (.neg (.eq (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero)) .zero)))
def f0301 : Formula 1 := (.ex (.eq (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one)) .zero))
def f0302 : Formula 1 := (.ex (.neg (.eq (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one)) .zero)))
def f0303 : Formula 1 := (.ex (.eq (.join (.meet .one (.neg (.var 1))) (.meet (.neg .one) (.var 1))) .zero))
def f0304 : Formula 1 := (.ex (.neg (.eq (.join (.meet .one (.neg (.var 1))) (.meet (.neg .one) (.var 1))) .zero)))
def f0305 : Formula 1 := (.ex (.eq (.join (.meet .one (.neg (.var 0))) (.meet (.neg .one) (.var 0))) .zero))
def f0306 : Formula 1 := (.ex (.neg (.eq (.join (.meet .one (.neg (.var 0))) (.meet (.neg .one) (.var 0))) .zero)))
def f0307 : Formula 1 := (.ex (.eq (.join (.meet (.var 1) (.neg .zero)) (.meet (.neg (.var 1)) .zero)) .zero))
def f0308 : Formula 1 := (.ex (.neg (.eq (.join (.meet (.var 1) (.neg .zero)) (.meet (.neg (.var 1)) .zero)) .zero)))
def f0309 : Formula 1 := (.ex (.eq (.join (.meet (.var 1) (.neg .one)) (.meet (.neg (.var 1)) .one)) .zero))
def f0310 : Formula 1 := (.ex (.neg (.eq (.join (.meet (.var 1) (.neg .one)) (.meet (.neg (.var 1)) .one)) .zero)))
def f0311 : Formula 1 := (.ex (.eq (.join (.meet (.var 1) (.neg (.var 1))) (.meet (.neg (.var 1)) (.var 1))) .zero))
def f0312 : Formula 1 := (.ex (.neg (.eq (.join (.meet (.var 1) (.neg (.var 1))) (.meet (.neg (.var 1)) (.var 1))) .zero)))
def f0313 : Formula 1 := (.ex (.eq (.join (.meet (.var 1) (.neg (.var 0))) (.meet (.neg (.var 1)) (.var 0))) .zero))
def f0314 : Formula 1 := (.ex (.neg (.eq (.join (.meet (.var 1) (.neg (.var 0))) (.meet (.neg (.var 1)) (.var 0))) .zero)))
def f0315 : Formula 1 := (.ex (.eq (.join (.meet (.var 0) (.neg .zero)) (.meet (.neg (.var 0)) .zero)) .zero))
def f0316 : Formula 1 := (.ex (.neg (.eq (.join (.meet (.var 0) (.neg .zero)) (.meet (.neg (.var 0)) .zero)) .zero)))
def f0317 : Formula 1 := (.ex (.eq (.join (.meet (.var 0) (.neg .one)) (.meet (.neg (.var 0)) .one)) .zero))
def f0318 : Formula 1 := (.ex (.neg (.eq (.join (.meet (.var 0) (.neg .one)) (.meet (.neg (.var 0)) .one)) .zero)))
def f0319 : Formula 1 := (.ex (.eq (.join (.meet (.var 0) (.neg (.var 1))) (.meet (.neg (.var 0)) (.var 1))) .zero))
def f0320 : Formula 1 := (.ex (.neg (.eq (.join (.meet (.var 0) (.neg (.var 1))) (.meet (.neg (.var 0)) (.var 1))) .zero)))
def f0321 : Formula 1 := (.ex (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero))
def f0322 : Formula 1 := (.ex (.neg (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero)))
def f0323 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) .zero) .zero)) (.neg (.eq (.meet (.neg (.var 0)) .zero) .zero))))
def f0324 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) .one) .zero)) (.neg (.eq (.meet (.neg (.var 0)) .one) .zero))))
def f0325 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.var 1)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.var 1)) .zero))))
def f0326 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.neg .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.neg .zero)) .zero))))
def f0327 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.neg .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.neg .one)) .zero))))
def f0328 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.neg (.var 1))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.neg (.var 1))) .zero))))
def f0329 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .zero .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .zero .zero)) .zero))))
def f0330 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .zero .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .zero .one)) .zero))))
def f0331 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .zero (.var 1))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .zero (.var 1))) .zero))))
def f0332 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .one .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .one .zero)) .zero))))
def f0333 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .one .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .one .one)) .zero))))
def f0334 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .one (.var 1))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .one (.var 1))) .zero))))
def f0335 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet (.var 1) .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet (.var 1) .zero)) .zero))))
def f0336 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet (.var 1) .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet (.var 1) .one)) .zero))))
def f0337 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet (.var 1) (.var 1))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet (.var 1) (.var 1))) .zero))))
def f0338 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .zero .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .zero .zero)) .zero))))
def f0339 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .zero .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .zero .one)) .zero))))
def f0340 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .zero (.var 1))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .zero (.var 1))) .zero))))
def f0341 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .one .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .one .zero)) .zero))))
def f0342 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .one .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .one .one)) .zero))))
def f0343 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .one (.var 1))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .one (.var 1))) .zero))))
def f0344 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.var 1) .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.var 1) .zero)) .zero))))
def f0345 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.var 1) .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.var 1) .one)) .zero))))
def f0346 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.var 1) (.var 1))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.var 1) (.var 1))) .zero))))
def f0347 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero))) .zero))))
def f0348 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one))) .zero))))
def f0349 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .zero (.neg (.var 1))) (.meet (.neg .zero) (.var 1)))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .zero (.neg (.var 1))) (.meet (.neg .zero) (.var 1)))) .zero))))
def f0350 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero))) .zero))))
def f0351 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one))) .zero))))
def f0352 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .one (.neg (.var 1))) (.meet (.neg .one) (.var 1)))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .one (.neg (.var 1))) (.meet (.neg .one) (.var 1)))) .zero))))
def f0353 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet (.var 1) (.neg .zero)) (.meet (.neg (.var 1)) .zero))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet (.var 1) (.neg .zero)) (.meet (.neg (.var 1)) .zero))) .zero))))
def f0354 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet (.var 1) (.neg .one)) (.meet (.neg (.var 1)) .one))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet (.var 1) (.neg .one)) (.meet (.neg (.var 1)) .one))) .zero))))
def f0355 : Formula 1 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet (.var 1) (.neg (.var 1))) (.meet (.neg (.var 1)) (.var 1)))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet (.var 1) (.neg (.var 1))) (.meet (.neg (.var 1)) (.var 1)))) .zero))))
def f0356 : Formula 2 := (.eq .zero .zero)
def f0357 : Formula 2 := (.neg (.eq .zero .zero))
def f0358 : Formula 2 := (.eq .one .zero)
def f0359 : Formula 2 := (.neg (.eq .one .zero))
def f0360 : Formula 2 := (.eq (.var 1) .zero)
def f0361 : Formula 2 := (.neg (.eq (.var 1) .zero))
def f0362 : Formula 2 := (.eq (.var 0) .zero)
def f0363 : Formula 2 := (.neg (.eq (.var 0) .zero))
def f0364 : Formula 2 := (.eq (.neg .zero) .zero)
def f0365 : Formula 2 := (.neg (.eq (.neg .zero) .zero))
def f0366 : Formula 2 := (.eq (.neg .one) .zero)
def f0367 : Formula 2 := (.neg (.eq (.neg .one) .zero))
def f0368 : Formula 2 := (.eq (.neg (.var 1)) .zero)
def f0369 : Formula 2 := (.neg (.eq (.neg (.var 1)) .zero))
def f0370 : Formula 2 := (.eq (.neg (.var 0)) .zero)
def f0371 : Formula 2 := (.neg (.eq (.neg (.var 0)) .zero))
def f0372 : Formula 2 := (.eq (.meet .zero .zero) .zero)
def f0373 : Formula 2 := (.neg (.eq (.meet .zero .zero) .zero))
def f0374 : Formula 2 := (.eq (.meet .zero .one) .zero)
def f0375 : Formula 2 := (.neg (.eq (.meet .zero .one) .zero))
def f0376 : Formula 2 := (.eq (.meet .zero (.var 1)) .zero)
def f0377 : Formula 2 := (.neg (.eq (.meet .zero (.var 1)) .zero))
def f0378 : Formula 2 := (.eq (.meet .zero (.var 0)) .zero)
def f0379 : Formula 2 := (.neg (.eq (.meet .zero (.var 0)) .zero))
def f0380 : Formula 2 := (.eq (.meet .one .zero) .zero)
def f0381 : Formula 2 := (.neg (.eq (.meet .one .zero) .zero))
def f0382 : Formula 2 := (.eq (.meet .one .one) .zero)
def f0383 : Formula 2 := (.neg (.eq (.meet .one .one) .zero))
def f0384 : Formula 2 := (.eq (.meet .one (.var 1)) .zero)
def f0385 : Formula 2 := (.neg (.eq (.meet .one (.var 1)) .zero))
def f0386 : Formula 2 := (.eq (.meet .one (.var 0)) .zero)
def f0387 : Formula 2 := (.neg (.eq (.meet .one (.var 0)) .zero))
def f0388 : Formula 2 := (.eq (.meet (.var 1) .zero) .zero)
def f0389 : Formula 2 := (.neg (.eq (.meet (.var 1) .zero) .zero))
def f0390 : Formula 2 := (.eq (.meet (.var 1) .one) .zero)
def f0391 : Formula 2 := (.neg (.eq (.meet (.var 1) .one) .zero))
def f0392 : Formula 2 := (.eq (.meet (.var 1) (.var 1)) .zero)
def f0393 : Formula 2 := (.neg (.eq (.meet (.var 1) (.var 1)) .zero))
def f0394 : Formula 2 := (.eq (.meet (.var 1) (.var 0)) .zero)
def f0395 : Formula 2 := (.neg (.eq (.meet (.var 1) (.var 0)) .zero))
def f0396 : Formula 2 := (.eq (.meet (.var 0) .zero) .zero)
def f0397 : Formula 2 := (.neg (.eq (.meet (.var 0) .zero) .zero))
def f0398 : Formula 2 := (.eq (.meet (.var 0) .one) .zero)
def f0399 : Formula 2 := (.neg (.eq (.meet (.var 0) .one) .zero))
def f0400 : Formula 2 := (.eq (.meet (.var 0) (.var 1)) .zero)
def f0401 : Formula 2 := (.neg (.eq (.meet (.var 0) (.var 1)) .zero))
def f0402 : Formula 2 := (.eq (.meet (.var 0) (.var 0)) .zero)
def f0403 : Formula 2 := (.neg (.eq (.meet (.var 0) (.var 0)) .zero))
def f0404 : Formula 2 := (.eq (.join .zero .zero) .zero)
def f0405 : Formula 2 := (.neg (.eq (.join .zero .zero) .zero))
def f0406 : Formula 2 := (.eq (.join .zero .one) .zero)
def f0407 : Formula 2 := (.neg (.eq (.join .zero .one) .zero))
def f0408 : Formula 2 := (.eq (.join .zero (.var 1)) .zero)
def f0409 : Formula 2 := (.neg (.eq (.join .zero (.var 1)) .zero))
def f0410 : Formula 2 := (.eq (.join .zero (.var 0)) .zero)
def f0411 : Formula 2 := (.neg (.eq (.join .zero (.var 0)) .zero))
def f0412 : Formula 2 := (.eq (.join .one .zero) .zero)
def f0413 : Formula 2 := (.neg (.eq (.join .one .zero) .zero))
def f0414 : Formula 2 := (.eq (.join .one .one) .zero)
def f0415 : Formula 2 := (.neg (.eq (.join .one .one) .zero))
def f0416 : Formula 2 := (.eq (.join .one (.var 1)) .zero)
def f0417 : Formula 2 := (.neg (.eq (.join .one (.var 1)) .zero))
def f0418 : Formula 2 := (.eq (.join .one (.var 0)) .zero)
def f0419 : Formula 2 := (.neg (.eq (.join .one (.var 0)) .zero))
def f0420 : Formula 2 := (.eq (.join (.var 1) .zero) .zero)
def f0421 : Formula 2 := (.neg (.eq (.join (.var 1) .zero) .zero))
def f0422 : Formula 2 := (.eq (.join (.var 1) .one) .zero)
def f0423 : Formula 2 := (.neg (.eq (.join (.var 1) .one) .zero))
def f0424 : Formula 2 := (.eq (.join (.var 1) (.var 1)) .zero)
def f0425 : Formula 2 := (.neg (.eq (.join (.var 1) (.var 1)) .zero))
def f0426 : Formula 2 := (.eq (.join (.var 1) (.var 0)) .zero)
def f0427 : Formula 2 := (.neg (.eq (.join (.var 1) (.var 0)) .zero))
def f0428 : Formula 2 := (.eq (.join (.var 0) .zero) .zero)
def f0429 : Formula 2 := (.neg (.eq (.join (.var 0) .zero) .zero))
def f0430 : Formula 2 := (.eq (.join (.var 0) .one) .zero)
def f0431 : Formula 2 := (.neg (.eq (.join (.var 0) .one) .zero))
def f0432 : Formula 2 := (.eq (.join (.var 0) (.var 1)) .zero)
def f0433 : Formula 2 := (.neg (.eq (.join (.var 0) (.var 1)) .zero))
def f0434 : Formula 2 := (.eq (.join (.var 0) (.var 0)) .zero)
def f0435 : Formula 2 := (.neg (.eq (.join (.var 0) (.var 0)) .zero))
def f0436 : Formula 2 := (.eq (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero)) .zero)
def f0437 : Formula 2 := (.neg (.eq (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero)) .zero))
def f0438 : Formula 2 := (.eq (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one)) .zero)
def f0439 : Formula 2 := (.neg (.eq (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one)) .zero))
def f0440 : Formula 2 := (.eq (.join (.meet .zero (.neg (.var 1))) (.meet (.neg .zero) (.var 1))) .zero)
def f0441 : Formula 2 := (.neg (.eq (.join (.meet .zero (.neg (.var 1))) (.meet (.neg .zero) (.var 1))) .zero))
def f0442 : Formula 2 := (.eq (.join (.meet .zero (.neg (.var 0))) (.meet (.neg .zero) (.var 0))) .zero)
def f0443 : Formula 2 := (.neg (.eq (.join (.meet .zero (.neg (.var 0))) (.meet (.neg .zero) (.var 0))) .zero))
def f0444 : Formula 2 := (.eq (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero)) .zero)
def f0445 : Formula 2 := (.neg (.eq (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero)) .zero))
def f0446 : Formula 2 := (.eq (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one)) .zero)
def f0447 : Formula 2 := (.neg (.eq (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one)) .zero))
def f0448 : Formula 2 := (.eq (.join (.meet .one (.neg (.var 1))) (.meet (.neg .one) (.var 1))) .zero)
def f0449 : Formula 2 := (.neg (.eq (.join (.meet .one (.neg (.var 1))) (.meet (.neg .one) (.var 1))) .zero))
def f0450 : Formula 2 := (.eq (.join (.meet .one (.neg (.var 0))) (.meet (.neg .one) (.var 0))) .zero)
def f0451 : Formula 2 := (.neg (.eq (.join (.meet .one (.neg (.var 0))) (.meet (.neg .one) (.var 0))) .zero))
def f0452 : Formula 2 := (.eq (.join (.meet (.var 1) (.neg .zero)) (.meet (.neg (.var 1)) .zero)) .zero)
def f0453 : Formula 2 := (.neg (.eq (.join (.meet (.var 1) (.neg .zero)) (.meet (.neg (.var 1)) .zero)) .zero))
def f0454 : Formula 2 := (.eq (.join (.meet (.var 1) (.neg .one)) (.meet (.neg (.var 1)) .one)) .zero)
def f0455 : Formula 2 := (.neg (.eq (.join (.meet (.var 1) (.neg .one)) (.meet (.neg (.var 1)) .one)) .zero))
def f0456 : Formula 2 := (.eq (.join (.meet (.var 1) (.neg (.var 1))) (.meet (.neg (.var 1)) (.var 1))) .zero)
def f0457 : Formula 2 := (.neg (.eq (.join (.meet (.var 1) (.neg (.var 1))) (.meet (.neg (.var 1)) (.var 1))) .zero))
def f0458 : Formula 2 := (.eq (.join (.meet (.var 1) (.neg (.var 0))) (.meet (.neg (.var 1)) (.var 0))) .zero)
def f0459 : Formula 2 := (.neg (.eq (.join (.meet (.var 1) (.neg (.var 0))) (.meet (.neg (.var 1)) (.var 0))) .zero))
def f0460 : Formula 2 := (.eq (.join (.meet (.var 0) (.neg .zero)) (.meet (.neg (.var 0)) .zero)) .zero)
def f0461 : Formula 2 := (.neg (.eq (.join (.meet (.var 0) (.neg .zero)) (.meet (.neg (.var 0)) .zero)) .zero))
def f0462 : Formula 2 := (.eq (.join (.meet (.var 0) (.neg .one)) (.meet (.neg (.var 0)) .one)) .zero)
def f0463 : Formula 2 := (.neg (.eq (.join (.meet (.var 0) (.neg .one)) (.meet (.neg (.var 0)) .one)) .zero))
def f0464 : Formula 2 := (.eq (.join (.meet (.var 0) (.neg (.var 1))) (.meet (.neg (.var 0)) (.var 1))) .zero)
def f0465 : Formula 2 := (.neg (.eq (.join (.meet (.var 0) (.neg (.var 1))) (.meet (.neg (.var 0)) (.var 1))) .zero))
def f0466 : Formula 2 := (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero)
def f0467 : Formula 2 := (.neg (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero))
def f0468 : Formula 2 := (.neg (.eq .zero .zero))
def f0469 : Formula 2 := (.conj (.eq .zero .zero) (.eq .zero .zero))
def f0470 : Formula 2 := (.disj (.eq .zero .zero) (.eq .zero .zero))
def f0471 : Formula 2 := (.conj (.eq .zero .zero) (.eq .one .zero))
def f0472 : Formula 2 := (.disj (.eq .zero .zero) (.eq .one .zero))
def f0473 : Formula 2 := (.conj (.eq .zero .zero) (.eq (.var 1) .zero))
def f0474 : Formula 2 := (.disj (.eq .zero .zero) (.eq (.var 1) .zero))
def f0475 : Formula 2 := (.conj (.eq .zero .zero) (.eq (.var 0) .zero))
def f0476 : Formula 2 := (.disj (.eq .zero .zero) (.eq (.var 0) .zero))
def f0477 : Formula 2 := (.neg (.eq .one .zero))
def f0478 : Formula 2 := (.conj (.eq .one .zero) (.eq .zero .zero))
def f0479 : Formula 2 := (.disj (.eq .one .zero) (.eq .zero .zero))
def f0480 : Formula 2 := (.conj (.eq .one .zero) (.eq .one .zero))
def f0481 : Formula 2 := (.disj (.eq .one .zero) (.eq .one .zero))
def f0482 : Formula 2 := (.conj (.eq .one .zero) (.eq (.var 1) .zero))
def f0483 : Formula 2 := (.disj (.eq .one .zero) (.eq (.var 1) .zero))
def f0484 : Formula 2 := (.conj (.eq .one .zero) (.eq (.var 0) .zero))
def f0485 : Formula 2 := (.disj (.eq .one .zero) (.eq (.var 0) .zero))
def f0486 : Formula 2 := (.neg (.eq (.var 1) .zero))
def f0487 : Formula 2 := (.conj (.eq (.var 1) .zero) (.eq .zero .zero))
def f0488 : Formula 2 := (.disj (.eq (.var 1) .zero) (.eq .zero .zero))
def f0489 : Formula 2 := (.conj (.eq (.var 1) .zero) (.eq .one .zero))
def f0490 : Formula 2 := (.disj (.eq (.var 1) .zero) (.eq .one .zero))
def f0491 : Formula 2 := (.conj (.eq (.var 1) .zero) (.eq (.var 1) .zero))
def f0492 : Formula 2 := (.disj (.eq (.var 1) .zero) (.eq (.var 1) .zero))
def f0493 : Formula 2 := (.conj (.eq (.var 1) .zero) (.eq (.var 0) .zero))
def f0494 : Formula 2 := (.disj (.eq (.var 1) .zero) (.eq (.var 0) .zero))
def f0495 : Formula 2 := (.neg (.eq (.var 0) .zero))
def f0496 : Formula 2 := (.conj (.eq (.var 0) .zero) (.eq .zero .zero))
def f0497 : Formula 2 := (.disj (.eq (.var 0) .zero) (.eq .zero .zero))
def f0498 : Formula 2 := (.conj (.eq (.var 0) .zero) (.eq .one .zero))
def f0499 : Formula 2 := (.disj (.eq (.var 0) .zero) (.eq .one .zero))
def f0500 : Formula 2 := (.conj (.eq (.var 0) .zero) (.eq (.var 1) .zero))
def f0501 : Formula 2 := (.disj (.eq (.var 0) .zero) (.eq (.var 1) .zero))
def f0502 : Formula 2 := (.conj (.eq (.var 0) .zero) (.eq (.var 0) .zero))
def f0503 : Formula 2 := (.disj (.eq (.var 0) .zero) (.eq (.var 0) .zero))
def f0504 : Formula 2 := (.ex (.eq .zero .zero))
def f0505 : Formula 2 := (.ex (.neg (.eq .zero .zero)))
def f0506 : Formula 2 := (.ex (.eq .one .zero))
def f0507 : Formula 2 := (.ex (.neg (.eq .one .zero)))
def f0508 : Formula 2 := (.ex (.eq (.var 2) .zero))
def f0509 : Formula 2 := (.ex (.neg (.eq (.var 2) .zero)))
def f0510 : Formula 2 := (.ex (.eq (.var 1) .zero))
def f0511 : Formula 2 := (.ex (.neg (.eq (.var 1) .zero)))
def f0512 : Formula 2 := (.ex (.eq (.var 0) .zero))
def f0513 : Formula 2 := (.ex (.neg (.eq (.var 0) .zero)))
def f0514 : Formula 2 := (.ex (.eq (.neg .zero) .zero))
def f0515 : Formula 2 := (.ex (.neg (.eq (.neg .zero) .zero)))
def f0516 : Formula 2 := (.ex (.eq (.neg .one) .zero))
def f0517 : Formula 2 := (.ex (.neg (.eq (.neg .one) .zero)))
def f0518 : Formula 2 := (.ex (.eq (.neg (.var 2)) .zero))
def f0519 : Formula 2 := (.ex (.neg (.eq (.neg (.var 2)) .zero)))
def f0520 : Formula 2 := (.ex (.eq (.neg (.var 1)) .zero))
def f0521 : Formula 2 := (.ex (.neg (.eq (.neg (.var 1)) .zero)))
def f0522 : Formula 2 := (.ex (.eq (.neg (.var 0)) .zero))
def f0523 : Formula 2 := (.ex (.neg (.eq (.neg (.var 0)) .zero)))
def f0524 : Formula 2 := (.ex (.eq (.meet .zero .zero) .zero))
def f0525 : Formula 2 := (.ex (.neg (.eq (.meet .zero .zero) .zero)))
def f0526 : Formula 2 := (.ex (.eq (.meet .zero .one) .zero))
def f0527 : Formula 2 := (.ex (.neg (.eq (.meet .zero .one) .zero)))
def f0528 : Formula 2 := (.ex (.eq (.meet .zero (.var 2)) .zero))
def f0529 : Formula 2 := (.ex (.neg (.eq (.meet .zero (.var 2)) .zero)))
def f0530 : Formula 2 := (.ex (.eq (.meet .zero (.var 1)) .zero))
def f0531 : Formula 2 := (.ex (.neg (.eq (.meet .zero (.var 1)) .zero)))
def f0532 : Formula 2 := (.ex (.eq (.meet .zero (.var 0)) .zero))
def f0533 : Formula 2 := (.ex (.neg (.eq (.meet .zero (.var 0)) .zero)))
def f0534 : Formula 2 := (.ex (.eq (.meet .one .zero) .zero))
def f0535 : Formula 2 := (.ex (.neg (.eq (.meet .one .zero) .zero)))
def f0536 : Formula 2 := (.ex (.eq (.meet .one .one) .zero))
def f0537 : Formula 2 := (.ex (.neg (.eq (.meet .one .one) .zero)))
def f0538 : Formula 2 := (.ex (.eq (.meet .one (.var 2)) .zero))
def f0539 : Formula 2 := (.ex (.neg (.eq (.meet .one (.var 2)) .zero)))
def f0540 : Formula 2 := (.ex (.eq (.meet .one (.var 1)) .zero))
def f0541 : Formula 2 := (.ex (.neg (.eq (.meet .one (.var 1)) .zero)))
def f0542 : Formula 2 := (.ex (.eq (.meet .one (.var 0)) .zero))
def f0543 : Formula 2 := (.ex (.neg (.eq (.meet .one (.var 0)) .zero)))
def f0544 : Formula 2 := (.ex (.eq (.meet (.var 2) .zero) .zero))
def f0545 : Formula 2 := (.ex (.neg (.eq (.meet (.var 2) .zero) .zero)))
def f0546 : Formula 2 := (.ex (.eq (.meet (.var 2) .one) .zero))
def f0547 : Formula 2 := (.ex (.neg (.eq (.meet (.var 2) .one) .zero)))
def f0548 : Formula 2 := (.ex (.eq (.meet (.var 2) (.var 2)) .zero))
def f0549 : Formula 2 := (.ex (.neg (.eq (.meet (.var 2) (.var 2)) .zero)))
def f0550 : Formula 2 := (.ex (.eq (.meet (.var 2) (.var 1)) .zero))
def f0551 : Formula 2 := (.ex (.neg (.eq (.meet (.var 2) (.var 1)) .zero)))
def f0552 : Formula 2 := (.ex (.eq (.meet (.var 2) (.var 0)) .zero))
def f0553 : Formula 2 := (.ex (.neg (.eq (.meet (.var 2) (.var 0)) .zero)))
def f0554 : Formula 2 := (.ex (.eq (.meet (.var 1) .zero) .zero))
def f0555 : Formula 2 := (.ex (.neg (.eq (.meet (.var 1) .zero) .zero)))
def f0556 : Formula 2 := (.ex (.eq (.meet (.var 1) .one) .zero))
def f0557 : Formula 2 := (.ex (.neg (.eq (.meet (.var 1) .one) .zero)))
def f0558 : Formula 2 := (.ex (.eq (.meet (.var 1) (.var 2)) .zero))
def f0559 : Formula 2 := (.ex (.neg (.eq (.meet (.var 1) (.var 2)) .zero)))
def f0560 : Formula 2 := (.ex (.eq (.meet (.var 1) (.var 1)) .zero))
def f0561 : Formula 2 := (.ex (.neg (.eq (.meet (.var 1) (.var 1)) .zero)))
def f0562 : Formula 2 := (.ex (.eq (.meet (.var 1) (.var 0)) .zero))
def f0563 : Formula 2 := (.ex (.neg (.eq (.meet (.var 1) (.var 0)) .zero)))
def f0564 : Formula 2 := (.ex (.eq (.meet (.var 0) .zero) .zero))
def f0565 : Formula 2 := (.ex (.neg (.eq (.meet (.var 0) .zero) .zero)))
def f0566 : Formula 2 := (.ex (.eq (.meet (.var 0) .one) .zero))
def f0567 : Formula 2 := (.ex (.neg (.eq (.meet (.var 0) .one) .zero)))
def f0568 : Formula 2 := (.ex (.eq (.meet (.var 0) (.var 2)) .zero))
def f0569 : Formula 2 := (.ex (.neg (.eq (.meet (.var 0) (.var 2)) .zero)))
def f0570 : Formula 2 := (.ex (.eq (.meet (.var 0) (.var 1)) .zero))
def f0571 : Formula 2 := (.ex (.neg (.eq (.meet (.var 0) (.var 1)) .zero)))
def f0572 : Formula 2 := (.ex (.eq (.meet (.var 0) (.var 0)) .zero))
def f0573 : Formula 2 := (.ex (.neg (.eq (.meet (.var 0) (.var 0)) .zero)))
def f0574 : Formula 2 := (.ex (.eq (.join .zero .zero) .zero))
def f0575 : Formula 2 := (.ex (.neg (.eq (.join .zero .zero) .zero)))
def f0576 : Formula 2 := (.ex (.eq (.join .zero .one) .zero))
def f0577 : Formula 2 := (.ex (.neg (.eq (.join .zero .one) .zero)))
def f0578 : Formula 2 := (.ex (.eq (.join .zero (.var 2)) .zero))
def f0579 : Formula 2 := (.ex (.neg (.eq (.join .zero (.var 2)) .zero)))
def f0580 : Formula 2 := (.ex (.eq (.join .zero (.var 1)) .zero))
def f0581 : Formula 2 := (.ex (.neg (.eq (.join .zero (.var 1)) .zero)))
def f0582 : Formula 2 := (.ex (.eq (.join .zero (.var 0)) .zero))
def f0583 : Formula 2 := (.ex (.neg (.eq (.join .zero (.var 0)) .zero)))
def f0584 : Formula 2 := (.ex (.eq (.join .one .zero) .zero))
def f0585 : Formula 2 := (.ex (.neg (.eq (.join .one .zero) .zero)))
def f0586 : Formula 2 := (.ex (.eq (.join .one .one) .zero))
def f0587 : Formula 2 := (.ex (.neg (.eq (.join .one .one) .zero)))
def f0588 : Formula 2 := (.ex (.eq (.join .one (.var 2)) .zero))
def f0589 : Formula 2 := (.ex (.neg (.eq (.join .one (.var 2)) .zero)))
def f0590 : Formula 2 := (.ex (.eq (.join .one (.var 1)) .zero))
def f0591 : Formula 2 := (.ex (.neg (.eq (.join .one (.var 1)) .zero)))
def f0592 : Formula 2 := (.ex (.eq (.join .one (.var 0)) .zero))
def f0593 : Formula 2 := (.ex (.neg (.eq (.join .one (.var 0)) .zero)))
def f0594 : Formula 2 := (.ex (.eq (.join (.var 2) .zero) .zero))
def f0595 : Formula 2 := (.ex (.neg (.eq (.join (.var 2) .zero) .zero)))
def f0596 : Formula 2 := (.ex (.eq (.join (.var 2) .one) .zero))
def f0597 : Formula 2 := (.ex (.neg (.eq (.join (.var 2) .one) .zero)))
def f0598 : Formula 2 := (.ex (.eq (.join (.var 2) (.var 2)) .zero))
def f0599 : Formula 2 := (.ex (.neg (.eq (.join (.var 2) (.var 2)) .zero)))
def f0600 : Formula 2 := (.ex (.eq (.join (.var 2) (.var 1)) .zero))
def f0601 : Formula 2 := (.ex (.neg (.eq (.join (.var 2) (.var 1)) .zero)))
def f0602 : Formula 2 := (.ex (.eq (.join (.var 2) (.var 0)) .zero))
def f0603 : Formula 2 := (.ex (.neg (.eq (.join (.var 2) (.var 0)) .zero)))
def f0604 : Formula 2 := (.ex (.eq (.join (.var 1) .zero) .zero))
def f0605 : Formula 2 := (.ex (.neg (.eq (.join (.var 1) .zero) .zero)))
def f0606 : Formula 2 := (.ex (.eq (.join (.var 1) .one) .zero))
def f0607 : Formula 2 := (.ex (.neg (.eq (.join (.var 1) .one) .zero)))
def f0608 : Formula 2 := (.ex (.eq (.join (.var 1) (.var 2)) .zero))
def f0609 : Formula 2 := (.ex (.neg (.eq (.join (.var 1) (.var 2)) .zero)))
def f0610 : Formula 2 := (.ex (.eq (.join (.var 1) (.var 1)) .zero))
def f0611 : Formula 2 := (.ex (.neg (.eq (.join (.var 1) (.var 1)) .zero)))
def f0612 : Formula 2 := (.ex (.eq (.join (.var 1) (.var 0)) .zero))
def f0613 : Formula 2 := (.ex (.neg (.eq (.join (.var 1) (.var 0)) .zero)))
def f0614 : Formula 2 := (.ex (.eq (.join (.var 0) .zero) .zero))
def f0615 : Formula 2 := (.ex (.neg (.eq (.join (.var 0) .zero) .zero)))
def f0616 : Formula 2 := (.ex (.eq (.join (.var 0) .one) .zero))
def f0617 : Formula 2 := (.ex (.neg (.eq (.join (.var 0) .one) .zero)))
def f0618 : Formula 2 := (.ex (.eq (.join (.var 0) (.var 2)) .zero))
def f0619 : Formula 2 := (.ex (.neg (.eq (.join (.var 0) (.var 2)) .zero)))
def f0620 : Formula 2 := (.ex (.eq (.join (.var 0) (.var 1)) .zero))
def f0621 : Formula 2 := (.ex (.neg (.eq (.join (.var 0) (.var 1)) .zero)))
def f0622 : Formula 2 := (.ex (.eq (.join (.var 0) (.var 0)) .zero))
def f0623 : Formula 2 := (.ex (.neg (.eq (.join (.var 0) (.var 0)) .zero)))
def f0624 : Formula 2 := (.ex (.eq (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero)) .zero))
def f0625 : Formula 2 := (.ex (.neg (.eq (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero)) .zero)))
def f0626 : Formula 2 := (.ex (.eq (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one)) .zero))
def f0627 : Formula 2 := (.ex (.neg (.eq (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one)) .zero)))
def f0628 : Formula 2 := (.ex (.eq (.join (.meet .zero (.neg (.var 2))) (.meet (.neg .zero) (.var 2))) .zero))
def f0629 : Formula 2 := (.ex (.neg (.eq (.join (.meet .zero (.neg (.var 2))) (.meet (.neg .zero) (.var 2))) .zero)))
def f0630 : Formula 2 := (.ex (.eq (.join (.meet .zero (.neg (.var 1))) (.meet (.neg .zero) (.var 1))) .zero))
def f0631 : Formula 2 := (.ex (.neg (.eq (.join (.meet .zero (.neg (.var 1))) (.meet (.neg .zero) (.var 1))) .zero)))
def f0632 : Formula 2 := (.ex (.eq (.join (.meet .zero (.neg (.var 0))) (.meet (.neg .zero) (.var 0))) .zero))
def f0633 : Formula 2 := (.ex (.neg (.eq (.join (.meet .zero (.neg (.var 0))) (.meet (.neg .zero) (.var 0))) .zero)))
def f0634 : Formula 2 := (.ex (.eq (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero)) .zero))
def f0635 : Formula 2 := (.ex (.neg (.eq (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero)) .zero)))
def f0636 : Formula 2 := (.ex (.eq (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one)) .zero))
def f0637 : Formula 2 := (.ex (.neg (.eq (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one)) .zero)))
def f0638 : Formula 2 := (.ex (.eq (.join (.meet .one (.neg (.var 2))) (.meet (.neg .one) (.var 2))) .zero))
def f0639 : Formula 2 := (.ex (.neg (.eq (.join (.meet .one (.neg (.var 2))) (.meet (.neg .one) (.var 2))) .zero)))
def f0640 : Formula 2 := (.ex (.eq (.join (.meet .one (.neg (.var 1))) (.meet (.neg .one) (.var 1))) .zero))
def f0641 : Formula 2 := (.ex (.neg (.eq (.join (.meet .one (.neg (.var 1))) (.meet (.neg .one) (.var 1))) .zero)))
def f0642 : Formula 2 := (.ex (.eq (.join (.meet .one (.neg (.var 0))) (.meet (.neg .one) (.var 0))) .zero))
def f0643 : Formula 2 := (.ex (.neg (.eq (.join (.meet .one (.neg (.var 0))) (.meet (.neg .one) (.var 0))) .zero)))
def f0644 : Formula 2 := (.ex (.eq (.join (.meet (.var 2) (.neg .zero)) (.meet (.neg (.var 2)) .zero)) .zero))
def f0645 : Formula 2 := (.ex (.neg (.eq (.join (.meet (.var 2) (.neg .zero)) (.meet (.neg (.var 2)) .zero)) .zero)))
def f0646 : Formula 2 := (.ex (.eq (.join (.meet (.var 2) (.neg .one)) (.meet (.neg (.var 2)) .one)) .zero))
def f0647 : Formula 2 := (.ex (.neg (.eq (.join (.meet (.var 2) (.neg .one)) (.meet (.neg (.var 2)) .one)) .zero)))
def f0648 : Formula 2 := (.ex (.eq (.join (.meet (.var 2) (.neg (.var 2))) (.meet (.neg (.var 2)) (.var 2))) .zero))
def f0649 : Formula 2 := (.ex (.neg (.eq (.join (.meet (.var 2) (.neg (.var 2))) (.meet (.neg (.var 2)) (.var 2))) .zero)))
def f0650 : Formula 2 := (.ex (.eq (.join (.meet (.var 2) (.neg (.var 1))) (.meet (.neg (.var 2)) (.var 1))) .zero))
def f0651 : Formula 2 := (.ex (.neg (.eq (.join (.meet (.var 2) (.neg (.var 1))) (.meet (.neg (.var 2)) (.var 1))) .zero)))
def f0652 : Formula 2 := (.ex (.eq (.join (.meet (.var 2) (.neg (.var 0))) (.meet (.neg (.var 2)) (.var 0))) .zero))
def f0653 : Formula 2 := (.ex (.neg (.eq (.join (.meet (.var 2) (.neg (.var 0))) (.meet (.neg (.var 2)) (.var 0))) .zero)))
def f0654 : Formula 2 := (.ex (.eq (.join (.meet (.var 1) (.neg .zero)) (.meet (.neg (.var 1)) .zero)) .zero))
def f0655 : Formula 2 := (.ex (.neg (.eq (.join (.meet (.var 1) (.neg .zero)) (.meet (.neg (.var 1)) .zero)) .zero)))
def f0656 : Formula 2 := (.ex (.eq (.join (.meet (.var 1) (.neg .one)) (.meet (.neg (.var 1)) .one)) .zero))
def f0657 : Formula 2 := (.ex (.neg (.eq (.join (.meet (.var 1) (.neg .one)) (.meet (.neg (.var 1)) .one)) .zero)))
def f0658 : Formula 2 := (.ex (.eq (.join (.meet (.var 1) (.neg (.var 2))) (.meet (.neg (.var 1)) (.var 2))) .zero))
def f0659 : Formula 2 := (.ex (.neg (.eq (.join (.meet (.var 1) (.neg (.var 2))) (.meet (.neg (.var 1)) (.var 2))) .zero)))
def f0660 : Formula 2 := (.ex (.eq (.join (.meet (.var 1) (.neg (.var 1))) (.meet (.neg (.var 1)) (.var 1))) .zero))
def f0661 : Formula 2 := (.ex (.neg (.eq (.join (.meet (.var 1) (.neg (.var 1))) (.meet (.neg (.var 1)) (.var 1))) .zero)))
def f0662 : Formula 2 := (.ex (.eq (.join (.meet (.var 1) (.neg (.var 0))) (.meet (.neg (.var 1)) (.var 0))) .zero))
def f0663 : Formula 2 := (.ex (.neg (.eq (.join (.meet (.var 1) (.neg (.var 0))) (.meet (.neg (.var 1)) (.var 0))) .zero)))
def f0664 : Formula 2 := (.ex (.eq (.join (.meet (.var 0) (.neg .zero)) (.meet (.neg (.var 0)) .zero)) .zero))
def f0665 : Formula 2 := (.ex (.neg (.eq (.join (.meet (.var 0) (.neg .zero)) (.meet (.neg (.var 0)) .zero)) .zero)))
def f0666 : Formula 2 := (.ex (.eq (.join (.meet (.var 0) (.neg .one)) (.meet (.neg (.var 0)) .one)) .zero))
def f0667 : Formula 2 := (.ex (.neg (.eq (.join (.meet (.var 0) (.neg .one)) (.meet (.neg (.var 0)) .one)) .zero)))
def f0668 : Formula 2 := (.ex (.eq (.join (.meet (.var 0) (.neg (.var 2))) (.meet (.neg (.var 0)) (.var 2))) .zero))
def f0669 : Formula 2 := (.ex (.neg (.eq (.join (.meet (.var 0) (.neg (.var 2))) (.meet (.neg (.var 0)) (.var 2))) .zero)))
def f0670 : Formula 2 := (.ex (.eq (.join (.meet (.var 0) (.neg (.var 1))) (.meet (.neg (.var 0)) (.var 1))) .zero))
def f0671 : Formula 2 := (.ex (.neg (.eq (.join (.meet (.var 0) (.neg (.var 1))) (.meet (.neg (.var 0)) (.var 1))) .zero)))
def f0672 : Formula 2 := (.ex (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero))
def f0673 : Formula 2 := (.ex (.neg (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero)))
def f0674 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) .zero) .zero)) (.neg (.eq (.meet (.neg (.var 0)) .zero) .zero))))
def f0675 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) .one) .zero)) (.neg (.eq (.meet (.neg (.var 0)) .one) .zero))))
def f0676 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.var 2)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.var 2)) .zero))))
def f0677 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.var 1)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.var 1)) .zero))))
def f0678 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.neg .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.neg .zero)) .zero))))
def f0679 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.neg .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.neg .one)) .zero))))
def f0680 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.neg (.var 2))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.neg (.var 2))) .zero))))
def f0681 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.neg (.var 1))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.neg (.var 1))) .zero))))
def f0682 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .zero .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .zero .zero)) .zero))))
def f0683 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .zero .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .zero .one)) .zero))))
def f0684 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .zero (.var 2))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .zero (.var 2))) .zero))))
def f0685 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .zero (.var 1))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .zero (.var 1))) .zero))))
def f0686 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .one .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .one .zero)) .zero))))
def f0687 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .one .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .one .one)) .zero))))
def f0688 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .one (.var 2))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .one (.var 2))) .zero))))
def f0689 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet .one (.var 1))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet .one (.var 1))) .zero))))
def f0690 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet (.var 2) .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet (.var 2) .zero)) .zero))))
def f0691 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet (.var 2) .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet (.var 2) .one)) .zero))))
def f0692 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet (.var 2) (.var 2))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet (.var 2) (.var 2))) .zero))))
def f0693 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet (.var 2) (.var 1))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet (.var 2) (.var 1))) .zero))))
def f0694 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet (.var 1) .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet (.var 1) .zero)) .zero))))
def f0695 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet (.var 1) .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet (.var 1) .one)) .zero))))
def f0696 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet (.var 1) (.var 2))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet (.var 1) (.var 2))) .zero))))
def f0697 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.meet (.var 1) (.var 1))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.meet (.var 1) (.var 1))) .zero))))
def f0698 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .zero .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .zero .zero)) .zero))))
def f0699 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .zero .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .zero .one)) .zero))))
def f0700 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .zero (.var 2))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .zero (.var 2))) .zero))))
def f0701 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .zero (.var 1))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .zero (.var 1))) .zero))))
def f0702 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .one .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .one .zero)) .zero))))
def f0703 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .one .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .one .one)) .zero))))
def f0704 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .one (.var 2))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .one (.var 2))) .zero))))
def f0705 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join .one (.var 1))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join .one (.var 1))) .zero))))
def f0706 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.var 2) .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.var 2) .zero)) .zero))))
def f0707 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.var 2) .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.var 2) .one)) .zero))))
def f0708 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.var 2) (.var 2))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.var 2) (.var 2))) .zero))))
def f0709 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.var 2) (.var 1))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.var 2) (.var 1))) .zero))))
def f0710 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.var 1) .zero)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.var 1) .zero)) .zero))))
def f0711 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.var 1) .one)) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.var 1) .one)) .zero))))
def f0712 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.var 1) (.var 2))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.var 1) (.var 2))) .zero))))
def f0713 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.var 1) (.var 1))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.var 1) (.var 1))) .zero))))
def f0714 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero))) .zero))))
def f0715 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one))) .zero))))
def f0716 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .zero (.neg (.var 2))) (.meet (.neg .zero) (.var 2)))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .zero (.neg (.var 2))) (.meet (.neg .zero) (.var 2)))) .zero))))
def f0717 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .zero (.neg (.var 1))) (.meet (.neg .zero) (.var 1)))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .zero (.neg (.var 1))) (.meet (.neg .zero) (.var 1)))) .zero))))
def f0718 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero))) .zero))))
def f0719 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one))) .zero))))
def f0720 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .one (.neg (.var 2))) (.meet (.neg .one) (.var 2)))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .one (.neg (.var 2))) (.meet (.neg .one) (.var 2)))) .zero))))
def f0721 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet .one (.neg (.var 1))) (.meet (.neg .one) (.var 1)))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet .one (.neg (.var 1))) (.meet (.neg .one) (.var 1)))) .zero))))
def f0722 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet (.var 2) (.neg .zero)) (.meet (.neg (.var 2)) .zero))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet (.var 2) (.neg .zero)) (.meet (.neg (.var 2)) .zero))) .zero))))
def f0723 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet (.var 2) (.neg .one)) (.meet (.neg (.var 2)) .one))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet (.var 2) (.neg .one)) (.meet (.neg (.var 2)) .one))) .zero))))
def f0724 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet (.var 2) (.neg (.var 2))) (.meet (.neg (.var 2)) (.var 2)))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet (.var 2) (.neg (.var 2))) (.meet (.neg (.var 2)) (.var 2)))) .zero))))
def f0725 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet (.var 2) (.neg (.var 1))) (.meet (.neg (.var 2)) (.var 1)))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet (.var 2) (.neg (.var 1))) (.meet (.neg (.var 2)) (.var 1)))) .zero))))
def f0726 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet (.var 1) (.neg .zero)) (.meet (.neg (.var 1)) .zero))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet (.var 1) (.neg .zero)) (.meet (.neg (.var 1)) .zero))) .zero))))
def f0727 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet (.var 1) (.neg .one)) (.meet (.neg (.var 1)) .one))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet (.var 1) (.neg .one)) (.meet (.neg (.var 1)) .one))) .zero))))
def f0728 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet (.var 1) (.neg (.var 2))) (.meet (.neg (.var 1)) (.var 2)))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet (.var 1) (.neg (.var 2))) (.meet (.neg (.var 1)) (.var 2)))) .zero))))
def f0729 : Formula 2 := (.ex (.conj (.neg (.eq (.meet (.var 0) (.join (.meet (.var 1) (.neg (.var 1))) (.meet (.neg (.var 1)) (.var 1)))) .zero)) (.neg (.eq (.meet (.neg (.var 0)) (.join (.meet (.var 1) (.neg (.var 1))) (.meet (.neg (.var 1)) (.var 1)))) .zero))))
def f0730 : Formula 0 := (.ex (.ex (.eq .zero .zero)))
def f0731 : Formula 0 := (.ex (.neg (.ex (.neg (.eq .zero .zero)))))
def f0732 : Formula 0 := (.ex (.ex (.eq .one .zero)))
def f0733 : Formula 0 := (.ex (.neg (.ex (.neg (.eq .one .zero)))))
def f0734 : Formula 0 := (.ex (.ex (.eq (.var 1) .zero)))
def f0735 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.var 1) .zero)))))
def f0736 : Formula 0 := (.ex (.ex (.eq (.var 0) .zero)))
def f0737 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.var 0) .zero)))))
def f0738 : Formula 0 := (.ex (.ex (.eq (.neg .zero) .zero)))
def f0739 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.neg .zero) .zero)))))
def f0740 : Formula 0 := (.ex (.ex (.eq (.neg .one) .zero)))
def f0741 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.neg .one) .zero)))))
def f0742 : Formula 0 := (.ex (.ex (.eq (.neg (.var 1)) .zero)))
def f0743 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.neg (.var 1)) .zero)))))
def f0744 : Formula 0 := (.ex (.ex (.eq (.neg (.var 0)) .zero)))
def f0745 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.neg (.var 0)) .zero)))))
def f0746 : Formula 0 := (.ex (.ex (.eq (.meet .zero .zero) .zero)))
def f0747 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.meet .zero .zero) .zero)))))
def f0748 : Formula 0 := (.ex (.ex (.eq (.meet .zero .one) .zero)))
def f0749 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.meet .zero .one) .zero)))))
def f0750 : Formula 0 := (.ex (.ex (.eq (.meet .zero (.var 1)) .zero)))
def f0751 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.meet .zero (.var 1)) .zero)))))
def f0752 : Formula 0 := (.ex (.ex (.eq (.meet .zero (.var 0)) .zero)))
def f0753 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.meet .zero (.var 0)) .zero)))))
def f0754 : Formula 0 := (.ex (.ex (.eq (.meet .one .zero) .zero)))
def f0755 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.meet .one .zero) .zero)))))
def f0756 : Formula 0 := (.ex (.ex (.eq (.meet .one .one) .zero)))
def f0757 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.meet .one .one) .zero)))))
def f0758 : Formula 0 := (.ex (.ex (.eq (.meet .one (.var 1)) .zero)))
def f0759 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.meet .one (.var 1)) .zero)))))
def f0760 : Formula 0 := (.ex (.ex (.eq (.meet .one (.var 0)) .zero)))
def f0761 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.meet .one (.var 0)) .zero)))))
def f0762 : Formula 0 := (.ex (.ex (.eq (.meet (.var 1) .zero) .zero)))
def f0763 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 1) .zero) .zero)))))
def f0764 : Formula 0 := (.ex (.ex (.eq (.meet (.var 1) .one) .zero)))
def f0765 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 1) .one) .zero)))))
def f0766 : Formula 0 := (.ex (.ex (.eq (.meet (.var 1) (.var 1)) .zero)))
def f0767 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 1) (.var 1)) .zero)))))
def f0768 : Formula 0 := (.ex (.ex (.eq (.meet (.var 1) (.var 0)) .zero)))
def f0769 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 1) (.var 0)) .zero)))))
def f0770 : Formula 0 := (.ex (.ex (.eq (.meet (.var 0) .zero) .zero)))
def f0771 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 0) .zero) .zero)))))
def f0772 : Formula 0 := (.ex (.ex (.eq (.meet (.var 0) .one) .zero)))
def f0773 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 0) .one) .zero)))))
def f0774 : Formula 0 := (.ex (.ex (.eq (.meet (.var 0) (.var 1)) .zero)))
def f0775 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 0) (.var 1)) .zero)))))
def f0776 : Formula 0 := (.ex (.ex (.eq (.meet (.var 0) (.var 0)) .zero)))
def f0777 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 0) (.var 0)) .zero)))))
def f0778 : Formula 0 := (.ex (.ex (.eq (.join .zero .zero) .zero)))
def f0779 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join .zero .zero) .zero)))))
def f0780 : Formula 0 := (.ex (.ex (.eq (.join .zero .one) .zero)))
def f0781 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join .zero .one) .zero)))))
def f0782 : Formula 0 := (.ex (.ex (.eq (.join .zero (.var 1)) .zero)))
def f0783 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join .zero (.var 1)) .zero)))))
def f0784 : Formula 0 := (.ex (.ex (.eq (.join .zero (.var 0)) .zero)))
def f0785 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join .zero (.var 0)) .zero)))))
def f0786 : Formula 0 := (.ex (.ex (.eq (.join .one .zero) .zero)))
def f0787 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join .one .zero) .zero)))))
def f0788 : Formula 0 := (.ex (.ex (.eq (.join .one .one) .zero)))
def f0789 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join .one .one) .zero)))))
def f0790 : Formula 0 := (.ex (.ex (.eq (.join .one (.var 1)) .zero)))
def f0791 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join .one (.var 1)) .zero)))))
def f0792 : Formula 0 := (.ex (.ex (.eq (.join .one (.var 0)) .zero)))
def f0793 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join .one (.var 0)) .zero)))))
def f0794 : Formula 0 := (.ex (.ex (.eq (.join (.var 1) .zero) .zero)))
def f0795 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.var 1) .zero) .zero)))))
def f0796 : Formula 0 := (.ex (.ex (.eq (.join (.var 1) .one) .zero)))
def f0797 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.var 1) .one) .zero)))))
def f0798 : Formula 0 := (.ex (.ex (.eq (.join (.var 1) (.var 1)) .zero)))
def f0799 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.var 1) (.var 1)) .zero)))))
def f0800 : Formula 0 := (.ex (.ex (.eq (.join (.var 1) (.var 0)) .zero)))
def f0801 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.var 1) (.var 0)) .zero)))))
def f0802 : Formula 0 := (.ex (.ex (.eq (.join (.var 0) .zero) .zero)))
def f0803 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.var 0) .zero) .zero)))))
def f0804 : Formula 0 := (.ex (.ex (.eq (.join (.var 0) .one) .zero)))
def f0805 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.var 0) .one) .zero)))))
def f0806 : Formula 0 := (.ex (.ex (.eq (.join (.var 0) (.var 1)) .zero)))
def f0807 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.var 0) (.var 1)) .zero)))))
def f0808 : Formula 0 := (.ex (.ex (.eq (.join (.var 0) (.var 0)) .zero)))
def f0809 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.var 0) (.var 0)) .zero)))))
def f0810 : Formula 0 := (.ex (.ex (.eq (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero)) .zero)))
def f0811 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero)) .zero)))))
def f0812 : Formula 0 := (.ex (.ex (.eq (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one)) .zero)))
def f0813 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one)) .zero)))))
def f0814 : Formula 0 := (.ex (.ex (.eq (.join (.meet .zero (.neg (.var 1))) (.meet (.neg .zero) (.var 1))) .zero)))
def f0815 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .zero (.neg (.var 1))) (.meet (.neg .zero) (.var 1))) .zero)))))
def f0816 : Formula 0 := (.ex (.ex (.eq (.join (.meet .zero (.neg (.var 0))) (.meet (.neg .zero) (.var 0))) .zero)))
def f0817 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .zero (.neg (.var 0))) (.meet (.neg .zero) (.var 0))) .zero)))))
def f0818 : Formula 0 := (.ex (.ex (.eq (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero)) .zero)))
def f0819 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero)) .zero)))))
def f0820 : Formula 0 := (.ex (.ex (.eq (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one)) .zero)))
def f0821 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one)) .zero)))))
def f0822 : Formula 0 := (.ex (.ex (.eq (.join (.meet .one (.neg (.var 1))) (.meet (.neg .one) (.var 1))) .zero)))
def f0823 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .one (.neg (.var 1))) (.meet (.neg .one) (.var 1))) .zero)))))
def f0824 : Formula 0 := (.ex (.ex (.eq (.join (.meet .one (.neg (.var 0))) (.meet (.neg .one) (.var 0))) .zero)))
def f0825 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .one (.neg (.var 0))) (.meet (.neg .one) (.var 0))) .zero)))))
def f0826 : Formula 0 := (.ex (.ex (.eq (.join (.meet (.var 1) (.neg .zero)) (.meet (.neg (.var 1)) .zero)) .zero)))
def f0827 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 1) (.neg .zero)) (.meet (.neg (.var 1)) .zero)) .zero)))))
def f0828 : Formula 0 := (.ex (.ex (.eq (.join (.meet (.var 1) (.neg .one)) (.meet (.neg (.var 1)) .one)) .zero)))
def f0829 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 1) (.neg .one)) (.meet (.neg (.var 1)) .one)) .zero)))))
def f0830 : Formula 0 := (.ex (.ex (.eq (.join (.meet (.var 1) (.neg (.var 1))) (.meet (.neg (.var 1)) (.var 1))) .zero)))
def f0831 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 1) (.neg (.var 1))) (.meet (.neg (.var 1)) (.var 1))) .zero)))))
def f0832 : Formula 0 := (.ex (.ex (.eq (.join (.meet (.var 1) (.neg (.var 0))) (.meet (.neg (.var 1)) (.var 0))) .zero)))
def f0833 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 1) (.neg (.var 0))) (.meet (.neg (.var 1)) (.var 0))) .zero)))))
def f0834 : Formula 0 := (.ex (.ex (.eq (.join (.meet (.var 0) (.neg .zero)) (.meet (.neg (.var 0)) .zero)) .zero)))
def f0835 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 0) (.neg .zero)) (.meet (.neg (.var 0)) .zero)) .zero)))))
def f0836 : Formula 0 := (.ex (.ex (.eq (.join (.meet (.var 0) (.neg .one)) (.meet (.neg (.var 0)) .one)) .zero)))
def f0837 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 0) (.neg .one)) (.meet (.neg (.var 0)) .one)) .zero)))))
def f0838 : Formula 0 := (.ex (.ex (.eq (.join (.meet (.var 0) (.neg (.var 1))) (.meet (.neg (.var 0)) (.var 1))) .zero)))
def f0839 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 0) (.neg (.var 1))) (.meet (.neg (.var 0)) (.var 1))) .zero)))))
def f0840 : Formula 0 := (.ex (.ex (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero)))
def f0841 : Formula 0 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero)))))
def f0842 : Formula 1 := (.ex (.ex (.eq .zero .zero)))
def f0843 : Formula 1 := (.ex (.neg (.ex (.neg (.eq .zero .zero)))))
def f0844 : Formula 1 := (.ex (.ex (.eq .one .zero)))
def f0845 : Formula 1 := (.ex (.neg (.ex (.neg (.eq .one .zero)))))
def f0846 : Formula 1 := (.ex (.ex (.eq (.var 2) .zero)))
def f0847 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.var 2) .zero)))))
def f0848 : Formula 1 := (.ex (.ex (.eq (.var 1) .zero)))
def f0849 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.var 1) .zero)))))
def f0850 : Formula 1 := (.ex (.ex (.eq (.var 0) .zero)))
def f0851 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.var 0) .zero)))))
def f0852 : Formula 1 := (.ex (.ex (.eq (.neg .zero) .zero)))
def f0853 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.neg .zero) .zero)))))
def f0854 : Formula 1 := (.ex (.ex (.eq (.neg .one) .zero)))
def f0855 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.neg .one) .zero)))))
def f0856 : Formula 1 := (.ex (.ex (.eq (.neg (.var 2)) .zero)))
def f0857 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.neg (.var 2)) .zero)))))
def f0858 : Formula 1 := (.ex (.ex (.eq (.neg (.var 1)) .zero)))
def f0859 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.neg (.var 1)) .zero)))))
def f0860 : Formula 1 := (.ex (.ex (.eq (.neg (.var 0)) .zero)))
def f0861 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.neg (.var 0)) .zero)))))
def f0862 : Formula 1 := (.ex (.ex (.eq (.meet .zero .zero) .zero)))
def f0863 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet .zero .zero) .zero)))))
def f0864 : Formula 1 := (.ex (.ex (.eq (.meet .zero .one) .zero)))
def f0865 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet .zero .one) .zero)))))
def f0866 : Formula 1 := (.ex (.ex (.eq (.meet .zero (.var 2)) .zero)))
def f0867 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet .zero (.var 2)) .zero)))))
def f0868 : Formula 1 := (.ex (.ex (.eq (.meet .zero (.var 1)) .zero)))
def f0869 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet .zero (.var 1)) .zero)))))
def f0870 : Formula 1 := (.ex (.ex (.eq (.meet .zero (.var 0)) .zero)))
def f0871 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet .zero (.var 0)) .zero)))))
def f0872 : Formula 1 := (.ex (.ex (.eq (.meet .one .zero) .zero)))
def f0873 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet .one .zero) .zero)))))
def f0874 : Formula 1 := (.ex (.ex (.eq (.meet .one .one) .zero)))
def f0875 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet .one .one) .zero)))))
def f0876 : Formula 1 := (.ex (.ex (.eq (.meet .one (.var 2)) .zero)))
def f0877 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet .one (.var 2)) .zero)))))
def f0878 : Formula 1 := (.ex (.ex (.eq (.meet .one (.var 1)) .zero)))
def f0879 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet .one (.var 1)) .zero)))))
def f0880 : Formula 1 := (.ex (.ex (.eq (.meet .one (.var 0)) .zero)))
def f0881 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet .one (.var 0)) .zero)))))
def f0882 : Formula 1 := (.ex (.ex (.eq (.meet (.var 2) .zero) .zero)))
def f0883 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 2) .zero) .zero)))))
def f0884 : Formula 1 := (.ex (.ex (.eq (.meet (.var 2) .one) .zero)))
def f0885 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 2) .one) .zero)))))
def f0886 : Formula 1 := (.ex (.ex (.eq (.meet (.var 2) (.var 2)) .zero)))
def f0887 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 2) (.var 2)) .zero)))))
def f0888 : Formula 1 := (.ex (.ex (.eq (.meet (.var 2) (.var 1)) .zero)))
def f0889 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 2) (.var 1)) .zero)))))
def f0890 : Formula 1 := (.ex (.ex (.eq (.meet (.var 2) (.var 0)) .zero)))
def f0891 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 2) (.var 0)) .zero)))))
def f0892 : Formula 1 := (.ex (.ex (.eq (.meet (.var 1) .zero) .zero)))
def f0893 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 1) .zero) .zero)))))
def f0894 : Formula 1 := (.ex (.ex (.eq (.meet (.var 1) .one) .zero)))
def f0895 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 1) .one) .zero)))))
def f0896 : Formula 1 := (.ex (.ex (.eq (.meet (.var 1) (.var 2)) .zero)))
def f0897 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 1) (.var 2)) .zero)))))
def f0898 : Formula 1 := (.ex (.ex (.eq (.meet (.var 1) (.var 1)) .zero)))
def f0899 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 1) (.var 1)) .zero)))))
def f0900 : Formula 1 := (.ex (.ex (.eq (.meet (.var 1) (.var 0)) .zero)))
def f0901 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 1) (.var 0)) .zero)))))
def f0902 : Formula 1 := (.ex (.ex (.eq (.meet (.var 0) .zero) .zero)))
def f0903 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 0) .zero) .zero)))))
def f0904 : Formula 1 := (.ex (.ex (.eq (.meet (.var 0) .one) .zero)))
def f0905 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 0) .one) .zero)))))
def f0906 : Formula 1 := (.ex (.ex (.eq (.meet (.var 0) (.var 2)) .zero)))
def f0907 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 0) (.var 2)) .zero)))))
def f0908 : Formula 1 := (.ex (.ex (.eq (.meet (.var 0) (.var 1)) .zero)))
def f0909 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 0) (.var 1)) .zero)))))
def f0910 : Formula 1 := (.ex (.ex (.eq (.meet (.var 0) (.var 0)) .zero)))
def f0911 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.meet (.var 0) (.var 0)) .zero)))))
def f0912 : Formula 1 := (.ex (.ex (.eq (.join .zero .zero) .zero)))
def f0913 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join .zero .zero) .zero)))))
def f0914 : Formula 1 := (.ex (.ex (.eq (.join .zero .one) .zero)))
def f0915 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join .zero .one) .zero)))))
def f0916 : Formula 1 := (.ex (.ex (.eq (.join .zero (.var 2)) .zero)))
def f0917 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join .zero (.var 2)) .zero)))))
def f0918 : Formula 1 := (.ex (.ex (.eq (.join .zero (.var 1)) .zero)))
def f0919 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join .zero (.var 1)) .zero)))))
def f0920 : Formula 1 := (.ex (.ex (.eq (.join .zero (.var 0)) .zero)))
def f0921 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join .zero (.var 0)) .zero)))))
def f0922 : Formula 1 := (.ex (.ex (.eq (.join .one .zero) .zero)))
def f0923 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join .one .zero) .zero)))))
def f0924 : Formula 1 := (.ex (.ex (.eq (.join .one .one) .zero)))
def f0925 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join .one .one) .zero)))))
def f0926 : Formula 1 := (.ex (.ex (.eq (.join .one (.var 2)) .zero)))
def f0927 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join .one (.var 2)) .zero)))))
def f0928 : Formula 1 := (.ex (.ex (.eq (.join .one (.var 1)) .zero)))
def f0929 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join .one (.var 1)) .zero)))))
def f0930 : Formula 1 := (.ex (.ex (.eq (.join .one (.var 0)) .zero)))
def f0931 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join .one (.var 0)) .zero)))))
def f0932 : Formula 1 := (.ex (.ex (.eq (.join (.var 2) .zero) .zero)))
def f0933 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.var 2) .zero) .zero)))))
def f0934 : Formula 1 := (.ex (.ex (.eq (.join (.var 2) .one) .zero)))
def f0935 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.var 2) .one) .zero)))))
def f0936 : Formula 1 := (.ex (.ex (.eq (.join (.var 2) (.var 2)) .zero)))
def f0937 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.var 2) (.var 2)) .zero)))))
def f0938 : Formula 1 := (.ex (.ex (.eq (.join (.var 2) (.var 1)) .zero)))
def f0939 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.var 2) (.var 1)) .zero)))))
def f0940 : Formula 1 := (.ex (.ex (.eq (.join (.var 2) (.var 0)) .zero)))
def f0941 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.var 2) (.var 0)) .zero)))))
def f0942 : Formula 1 := (.ex (.ex (.eq (.join (.var 1) .zero) .zero)))
def f0943 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.var 1) .zero) .zero)))))
def f0944 : Formula 1 := (.ex (.ex (.eq (.join (.var 1) .one) .zero)))
def f0945 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.var 1) .one) .zero)))))
def f0946 : Formula 1 := (.ex (.ex (.eq (.join (.var 1) (.var 2)) .zero)))
def f0947 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.var 1) (.var 2)) .zero)))))
def f0948 : Formula 1 := (.ex (.ex (.eq (.join (.var 1) (.var 1)) .zero)))
def f0949 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.var 1) (.var 1)) .zero)))))
def f0950 : Formula 1 := (.ex (.ex (.eq (.join (.var 1) (.var 0)) .zero)))
def f0951 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.var 1) (.var 0)) .zero)))))
def f0952 : Formula 1 := (.ex (.ex (.eq (.join (.var 0) .zero) .zero)))
def f0953 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.var 0) .zero) .zero)))))
def f0954 : Formula 1 := (.ex (.ex (.eq (.join (.var 0) .one) .zero)))
def f0955 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.var 0) .one) .zero)))))
def f0956 : Formula 1 := (.ex (.ex (.eq (.join (.var 0) (.var 2)) .zero)))
def f0957 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.var 0) (.var 2)) .zero)))))
def f0958 : Formula 1 := (.ex (.ex (.eq (.join (.var 0) (.var 1)) .zero)))
def f0959 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.var 0) (.var 1)) .zero)))))
def f0960 : Formula 1 := (.ex (.ex (.eq (.join (.var 0) (.var 0)) .zero)))
def f0961 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.var 0) (.var 0)) .zero)))))
def f0962 : Formula 1 := (.ex (.ex (.eq (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero)) .zero)))
def f0963 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .zero (.neg .zero)) (.meet (.neg .zero) .zero)) .zero)))))
def f0964 : Formula 1 := (.ex (.ex (.eq (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one)) .zero)))
def f0965 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .zero (.neg .one)) (.meet (.neg .zero) .one)) .zero)))))
def f0966 : Formula 1 := (.ex (.ex (.eq (.join (.meet .zero (.neg (.var 2))) (.meet (.neg .zero) (.var 2))) .zero)))
def f0967 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .zero (.neg (.var 2))) (.meet (.neg .zero) (.var 2))) .zero)))))
def f0968 : Formula 1 := (.ex (.ex (.eq (.join (.meet .zero (.neg (.var 1))) (.meet (.neg .zero) (.var 1))) .zero)))
def f0969 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .zero (.neg (.var 1))) (.meet (.neg .zero) (.var 1))) .zero)))))
def f0970 : Formula 1 := (.ex (.ex (.eq (.join (.meet .zero (.neg (.var 0))) (.meet (.neg .zero) (.var 0))) .zero)))
def f0971 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .zero (.neg (.var 0))) (.meet (.neg .zero) (.var 0))) .zero)))))
def f0972 : Formula 1 := (.ex (.ex (.eq (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero)) .zero)))
def f0973 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .one (.neg .zero)) (.meet (.neg .one) .zero)) .zero)))))
def f0974 : Formula 1 := (.ex (.ex (.eq (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one)) .zero)))
def f0975 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .one (.neg .one)) (.meet (.neg .one) .one)) .zero)))))
def f0976 : Formula 1 := (.ex (.ex (.eq (.join (.meet .one (.neg (.var 2))) (.meet (.neg .one) (.var 2))) .zero)))
def f0977 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .one (.neg (.var 2))) (.meet (.neg .one) (.var 2))) .zero)))))
def f0978 : Formula 1 := (.ex (.ex (.eq (.join (.meet .one (.neg (.var 1))) (.meet (.neg .one) (.var 1))) .zero)))
def f0979 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .one (.neg (.var 1))) (.meet (.neg .one) (.var 1))) .zero)))))
def f0980 : Formula 1 := (.ex (.ex (.eq (.join (.meet .one (.neg (.var 0))) (.meet (.neg .one) (.var 0))) .zero)))
def f0981 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet .one (.neg (.var 0))) (.meet (.neg .one) (.var 0))) .zero)))))
def f0982 : Formula 1 := (.ex (.ex (.eq (.join (.meet (.var 2) (.neg .zero)) (.meet (.neg (.var 2)) .zero)) .zero)))
def f0983 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 2) (.neg .zero)) (.meet (.neg (.var 2)) .zero)) .zero)))))
def f0984 : Formula 1 := (.ex (.ex (.eq (.join (.meet (.var 2) (.neg .one)) (.meet (.neg (.var 2)) .one)) .zero)))
def f0985 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 2) (.neg .one)) (.meet (.neg (.var 2)) .one)) .zero)))))
def f0986 : Formula 1 := (.ex (.ex (.eq (.join (.meet (.var 2) (.neg (.var 2))) (.meet (.neg (.var 2)) (.var 2))) .zero)))
def f0987 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 2) (.neg (.var 2))) (.meet (.neg (.var 2)) (.var 2))) .zero)))))
def f0988 : Formula 1 := (.ex (.ex (.eq (.join (.meet (.var 2) (.neg (.var 1))) (.meet (.neg (.var 2)) (.var 1))) .zero)))
def f0989 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 2) (.neg (.var 1))) (.meet (.neg (.var 2)) (.var 1))) .zero)))))
def f0990 : Formula 1 := (.ex (.ex (.eq (.join (.meet (.var 2) (.neg (.var 0))) (.meet (.neg (.var 2)) (.var 0))) .zero)))
def f0991 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 2) (.neg (.var 0))) (.meet (.neg (.var 2)) (.var 0))) .zero)))))
def f0992 : Formula 1 := (.ex (.ex (.eq (.join (.meet (.var 1) (.neg .zero)) (.meet (.neg (.var 1)) .zero)) .zero)))
def f0993 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 1) (.neg .zero)) (.meet (.neg (.var 1)) .zero)) .zero)))))
def f0994 : Formula 1 := (.ex (.ex (.eq (.join (.meet (.var 1) (.neg .one)) (.meet (.neg (.var 1)) .one)) .zero)))
def f0995 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 1) (.neg .one)) (.meet (.neg (.var 1)) .one)) .zero)))))
def f0996 : Formula 1 := (.ex (.ex (.eq (.join (.meet (.var 1) (.neg (.var 2))) (.meet (.neg (.var 1)) (.var 2))) .zero)))
def f0997 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 1) (.neg (.var 2))) (.meet (.neg (.var 1)) (.var 2))) .zero)))))
def f0998 : Formula 1 := (.ex (.ex (.eq (.join (.meet (.var 1) (.neg (.var 1))) (.meet (.neg (.var 1)) (.var 1))) .zero)))
def f0999 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 1) (.neg (.var 1))) (.meet (.neg (.var 1)) (.var 1))) .zero)))))
def f1000 : Formula 1 := (.ex (.ex (.eq (.join (.meet (.var 1) (.neg (.var 0))) (.meet (.neg (.var 1)) (.var 0))) .zero)))
def f1001 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 1) (.neg (.var 0))) (.meet (.neg (.var 1)) (.var 0))) .zero)))))
def f1002 : Formula 1 := (.ex (.ex (.eq (.join (.meet (.var 0) (.neg .zero)) (.meet (.neg (.var 0)) .zero)) .zero)))
def f1003 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 0) (.neg .zero)) (.meet (.neg (.var 0)) .zero)) .zero)))))
def f1004 : Formula 1 := (.ex (.ex (.eq (.join (.meet (.var 0) (.neg .one)) (.meet (.neg (.var 0)) .one)) .zero)))
def f1005 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 0) (.neg .one)) (.meet (.neg (.var 0)) .one)) .zero)))))
def f1006 : Formula 1 := (.ex (.ex (.eq (.join (.meet (.var 0) (.neg (.var 2))) (.meet (.neg (.var 0)) (.var 2))) .zero)))
def f1007 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 0) (.neg (.var 2))) (.meet (.neg (.var 0)) (.var 2))) .zero)))))
def f1008 : Formula 1 := (.ex (.ex (.eq (.join (.meet (.var 0) (.neg (.var 1))) (.meet (.neg (.var 0)) (.var 1))) .zero)))
def f1009 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 0) (.neg (.var 1))) (.meet (.neg (.var 0)) (.var 1))) .zero)))))
def f1010 : Formula 1 := (.ex (.ex (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero)))
def f1011 : Formula 1 := (.ex (.neg (.ex (.neg (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero)))))
def f1012 : Formula 1 := (.ex (.ex (.neg (.eq (.var 0) .zero))))
def f1013 : Formula 1 := (.ex (.ex (.neg (.eq (.var 1) .zero))))
def f1014 : Formula 1 := (.ex (.ex (.neg (.eq (.var 0) .zero))))
def f1015 : Formula 1 := (.ex (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero))
def f1016 : Formula 2 := (.ex (.eq (.join (.meet (.var 0) (.neg (.var 1))) (.meet (.neg (.var 0)) (.var 1))) .zero))
def f1017 : Formula 2 := (.ex (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero))
def f1018 : Formula 2 := (.ex (.eq (.join (.meet (.var 0) (.neg (.var 1))) (.meet (.neg (.var 0)) (.var 1))) .zero))
def f1019 : Formula 2 := (.ex (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero))
def f1020 : Formula 2 := (.ex (.eq (.join (.meet (.var 0) (.neg (.var 1))) (.meet (.neg (.var 0)) (.var 1))) .zero))
def f1021 : Formula 2 := (.ex (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero))
def f1022 : Formula 2 := (.ex (.eq (.join (.meet (.var 0) (.neg (.var 1))) (.meet (.neg (.var 0)) (.var 1))) .zero))
def f1023 : Formula 2 := (.ex (.eq (.join (.meet (.var 0) (.neg (.var 0))) (.meet (.neg (.var 0)) (.var 0))) .zero))
def f1024 : Formula 3 := (.neg (.eq (.join (.meet (.var 2) (.var 1)) (.meet (.var 2) (.var 0))) .zero))
def f1025 : Formula 3 := (.eq .zero .zero)
def f1026 : Formula 3 := (.neg (.eq .zero .zero))
def f1027 : Formula 3 := (.neg (.eq (.var 2) .zero))
def f1028 : Formula 3 := (.eq (.var 2) .zero)
def f1029 : Formula 3 := (.neg (.eq (.neg (.var 2)) .zero))
def f1030 : Formula 3 := (.eq (.neg (.var 2)) .zero)
def f1031 : Formula 3 := (.neg (.eq (.var 1) .zero))
def f1032 : Formula 3 := (.eq (.var 1) .zero)
def f1033 : Formula 3 := (.neg (.eq (.neg (.var 1)) .zero))
def f1034 : Formula 3 := (.eq (.neg (.var 1)) .zero)
def f1035 : Formula 3 := (.neg (.eq (.var 0) .zero))
def f1036 : Formula 3 := (.eq (.var 0) .zero)
def f1037 : Formula 3 := (.neg (.eq (.neg (.var 0)) .zero))
def f1038 : Formula 3 := (.eq (.neg (.var 0)) .zero)
def f1039 : Formula 3 := (.eq (.join (.meet (.var 2) (.var 1)) (.meet (.var 2) (.var 0))) .zero)
def f1040 : Formula 2 := (.neg (.eq (.meet (.var 1) (.join (.var 1) (.var 0))) .zero))
def f1041 : Formula 2 := (.eq .zero .zero)
def f1042 : Formula 2 := (.neg (.eq .zero .zero))
def f1043 : Formula 2 := (.eq (.meet (.var 1) (.join (.var 1) (.var 0))) .zero)
def f1044 : Formula 1 := (.neg (.eq (.join (.var 0) (.neg (.var 0))) .zero))
def f1045 : Formula 1 := (.eq .zero .zero)
def f1046 : Formula 1 := (.neg (.eq .zero .zero))
def f1047 : Formula 1 := (.neg (.eq (.meet (.var 0) (.neg (.var 0))) .zero))
def f1048 : Formula 1 := (.neg (.eq (.neg (.neg (.var 0))) .zero))
def f1049 : Formula 2 := (.eq (.neg (.meet (.var 1) (.var 0))) .zero)
def f1050 : Formula 1 := (.neg (.eq (.meet (.join (.var 0) .zero) .one) .zero))
def f1051 : Formula 2 := (.conj (.neg (.eq (.var 1) .zero)) (.disj (.neg (.eq (.var 1) .zero)) (.neg (.eq (.var 0) .zero))))
def f1052 : Formula 1 := (.disj (.eq (.var 0) .zero) (.neg (.eq (.var 0) .zero)))
def f1053 : Formula 1 := (.conj (.eq (.var 0) .zero) (.neg (.eq (.var 0) .zero)))
def f1054 : Formula 2 := (.neg (.conj (.neg (.eq (.var 1) .zero)) (.neg (.eq (.var 0) .zero))))
def f1055 : Formula 2 := (.disj (.conj (.neg (.eq (.var 1) .zero)) (.neg (.eq (.var 0) .zero))) (.conj (.neg (.eq (.var 1) .zero)) (.neg (.eq (.var 0) .zero))))
def f1056 : Formula 1 := (.conj (.eq .zero .zero) (.neg (.eq (.var 0) .zero)))
def f1057 : Formula 1 := (.ex (.conj (.neg (.eq (.var 0) .zero)) (.conj (.eq (.meet (.var 0) (.neg (.var 1))) .zero) (.neg (.eq (.meet (.var 1) (.neg (.var 0))) .zero)))))
def f1058 : Formula 1 := (.ex (.conj (.conj (.neg (.eq (.var 0) .zero)) (.conj (.eq (.meet (.var 0) (.neg (.var 1))) .zero) (.neg (.eq (.meet (.var 1) (.neg (.var 0))) .zero)))) (.disj (.eq (.var 1) .zero) (.neg (.eq (.var 1) .zero)))))
def f1059 : Formula 1 := (.ex (.conj (.neg (.eq (.var 0) .zero)) (.eq (.meet (.var 0) (.neg (.var 1))) .zero)))
def f1060 : Formula 1 := (.ex (.conj (.neg (.eq (.var 0) .zero)) (.eq (.meet (.var 0) (.var 1)) .zero)))
def f1061 : Formula 0 := (.ex (.conj (.neg (.eq (.var 0) .zero)) (.neg (.eq (.neg (.var 0)) .zero))))
def f1062 : Formula 0 := (.eq .zero .zero)
def f1063 : Formula 0 := (.neg (.eq .zero .zero))
def f1064 : Formula 0 := (.ex (.conj (.eq (.var 0) .zero) (.neg (.eq (.var 0) .zero))))
def f1065 : Formula 1 := (.conj (.neg (.eq (.var 0) .zero)) (.neg (.eq (.neg (.var 0)) .zero)))
def f1066 : Formula 1 := (.disj (.eq (.var 0) .zero) (.eq (.neg (.var 0)) .zero))
def f1067 : Formula 2 := (.eq (.join (.neg (.var 0)) (.neg (.var 1))) .zero)
def f1068 : Formula 1 := (.disj (.eq (.neg (.var 0)) .zero) (.eq (.var 0) .zero))
def f1069 : Formula 3 := (.neg (.eq (.join (.meet (.var 1) (.var 2)) (.meet (.meet (.neg (.var 1)) (.var 2)) (.var 0))) .zero))
def f1070 : Formula 3 := (.eq (.join (.meet (.var 1) (.var 2)) (.meet (.meet (.neg (.var 1)) (.var 2)) (.var 0))) .zero)
def f1071 : Formula 2 := (.conj (.neg (.eq (.var 0) .zero)) (.neg (.eq (.var 1) .zero)))
def f1072 : Formula 1 := (.conj (.neg (.eq (.neg (.var 0)) .zero)) (.neg (.eq (.var 0) .zero)))

def runChunk0 : IO Unit := do
  resultLine "f0000" f0000
  resultLine "f0001" f0001
  resultLine "f0002" f0002
  resultLine "f0003" f0003
  resultLine "f0004" f0004
  resultLine "f0005" f0005
  resultLine "f0006" f0006
  resultLine "f0007" f0007
  resultLine "f0008" f0008
  resultLine "f0009" f0009
  resultLine "f0010" f0010
  resultLine "f0011" f0011
  resultLine "f0012" f0012
  resultLine "f0013" f0013
  resultLine "f0014" f0014
  resultLine "f0015" f0015
  resultLine "f0016" f0016
  resultLine "f0017" f0017
  resultLine "f0018" f0018
  resultLine "f0019" f0019
  resultLine "f0020" f0020
  resultLine "f0021" f0021
  resultLine "f0022" f0022
  resultLine "f0023" f0023
  resultLine "f0024" f0024
  resultLine "f0025" f0025
  resultLine "f0026" f0026
  resultLine "f0027" f0027
  resultLine "f0028" f0028
  resultLine "f0029" f0029
  resultLine "f0030" f0030
  resultLine "f0031" f0031
  resultLine "f0032" f0032
  resultLine "f0033" f0033
  resultLine "f0034" f0034
  resultLine "f0035" f0035
  resultLine "f0036" f0036
  resultLine "f0037" f0037
  resultLine "f0038" f0038
  resultLine "f0039" f0039
  resultLine "f0040" f0040
  resultLine "f0041" f0041
  resultLine "f0042" f0042
  resultLine "f0043" f0043
  resultLine "f0044" f0044
  resultLine "f0045" f0045
  resultLine "f0046" f0046
  resultLine "f0047" f0047
  resultLine "f0048" f0048
  resultLine "f0049" f0049

def runChunk1 : IO Unit := do
  resultLine "f0050" f0050
  resultLine "f0051" f0051
  resultLine "f0052" f0052
  resultLine "f0053" f0053
  resultLine "f0054" f0054
  resultLine "f0055" f0055
  resultLine "f0056" f0056
  resultLine "f0057" f0057
  resultLine "f0058" f0058
  resultLine "f0059" f0059
  resultLine "f0060" f0060
  resultLine "f0061" f0061
  resultLine "f0062" f0062
  resultLine "f0063" f0063
  resultLine "f0064" f0064
  resultLine "f0065" f0065
  resultLine "f0066" f0066
  resultLine "f0067" f0067
  resultLine "f0068" f0068
  resultLine "f0069" f0069
  resultLine "f0070" f0070
  resultLine "f0071" f0071
  resultLine "f0072" f0072
  resultLine "f0073" f0073
  resultLine "f0074" f0074
  resultLine "f0075" f0075
  resultLine "f0076" f0076
  resultLine "f0077" f0077
  resultLine "f0078" f0078
  resultLine "f0079" f0079
  resultLine "f0080" f0080
  resultLine "f0081" f0081
  resultLine "f0082" f0082
  resultLine "f0083" f0083
  resultLine "f0084" f0084
  resultLine "f0085" f0085
  resultLine "f0086" f0086
  resultLine "f0087" f0087
  resultLine "f0088" f0088
  resultLine "f0089" f0089
  resultLine "f0090" f0090
  resultLine "f0091" f0091
  resultLine "f0092" f0092
  resultLine "f0093" f0093
  resultLine "f0094" f0094
  resultLine "f0095" f0095
  resultLine "f0096" f0096
  resultLine "f0097" f0097
  resultLine "f0098" f0098
  resultLine "f0099" f0099

def runChunk2 : IO Unit := do
  resultLine "f0100" f0100
  resultLine "f0101" f0101
  resultLine "f0102" f0102
  resultLine "f0103" f0103
  resultLine "f0104" f0104
  resultLine "f0105" f0105
  resultLine "f0106" f0106
  resultLine "f0107" f0107
  resultLine "f0108" f0108
  resultLine "f0109" f0109
  resultLine "f0110" f0110
  resultLine "f0111" f0111
  resultLine "f0112" f0112
  resultLine "f0113" f0113
  resultLine "f0114" f0114
  resultLine "f0115" f0115
  resultLine "f0116" f0116
  resultLine "f0117" f0117
  resultLine "f0118" f0118
  resultLine "f0119" f0119
  resultLine "f0120" f0120
  resultLine "f0121" f0121
  resultLine "f0122" f0122
  resultLine "f0123" f0123
  resultLine "f0124" f0124
  resultLine "f0125" f0125
  resultLine "f0126" f0126
  resultLine "f0127" f0127
  resultLine "f0128" f0128
  resultLine "f0129" f0129
  resultLine "f0130" f0130
  resultLine "f0131" f0131
  resultLine "f0132" f0132
  resultLine "f0133" f0133
  resultLine "f0134" f0134
  resultLine "f0135" f0135
  resultLine "f0136" f0136
  resultLine "f0137" f0137
  resultLine "f0138" f0138
  resultLine "f0139" f0139
  resultLine "f0140" f0140
  resultLine "f0141" f0141
  resultLine "f0142" f0142
  resultLine "f0143" f0143
  resultLine "f0144" f0144
  resultLine "f0145" f0145
  resultLine "f0146" f0146
  resultLine "f0147" f0147
  resultLine "f0148" f0148
  resultLine "f0149" f0149

def runChunk3 : IO Unit := do
  resultLine "f0150" f0150
  resultLine "f0151" f0151
  resultLine "f0152" f0152
  resultLine "f0153" f0153
  resultLine "f0154" f0154
  resultLine "f0155" f0155
  resultLine "f0156" f0156
  resultLine "f0157" f0157
  resultLine "f0158" f0158
  resultLine "f0159" f0159
  resultLine "f0160" f0160
  resultLine "f0161" f0161
  resultLine "f0162" f0162
  resultLine "f0163" f0163
  resultLine "f0164" f0164
  resultLine "f0165" f0165
  resultLine "f0166" f0166
  resultLine "f0167" f0167
  resultLine "f0168" f0168
  resultLine "f0169" f0169
  resultLine "f0170" f0170
  resultLine "f0171" f0171
  resultLine "f0172" f0172
  resultLine "f0173" f0173
  resultLine "f0174" f0174
  resultLine "f0175" f0175
  resultLine "f0176" f0176
  resultLine "f0177" f0177
  resultLine "f0178" f0178
  resultLine "f0179" f0179
  resultLine "f0180" f0180
  resultLine "f0181" f0181
  resultLine "f0182" f0182
  resultLine "f0183" f0183
  resultLine "f0184" f0184
  resultLine "f0185" f0185
  resultLine "f0186" f0186
  resultLine "f0187" f0187
  resultLine "f0188" f0188
  resultLine "f0189" f0189
  resultLine "f0190" f0190
  resultLine "f0191" f0191
  resultLine "f0192" f0192
  resultLine "f0193" f0193
  resultLine "f0194" f0194
  resultLine "f0195" f0195
  resultLine "f0196" f0196
  resultLine "f0197" f0197
  resultLine "f0198" f0198
  resultLine "f0199" f0199

def runChunk4 : IO Unit := do
  resultLine "f0200" f0200
  resultLine "f0201" f0201
  resultLine "f0202" f0202
  resultLine "f0203" f0203
  resultLine "f0204" f0204
  resultLine "f0205" f0205
  resultLine "f0206" f0206
  resultLine "f0207" f0207
  resultLine "f0208" f0208
  resultLine "f0209" f0209
  resultLine "f0210" f0210
  resultLine "f0211" f0211
  resultLine "f0212" f0212
  resultLine "f0213" f0213
  resultLine "f0214" f0214
  resultLine "f0215" f0215
  resultLine "f0216" f0216
  resultLine "f0217" f0217
  resultLine "f0218" f0218
  resultLine "f0219" f0219
  resultLine "f0220" f0220
  resultLine "f0221" f0221
  resultLine "f0222" f0222
  resultLine "f0223" f0223
  resultLine "f0224" f0224
  resultLine "f0225" f0225
  resultLine "f0226" f0226
  resultLine "f0227" f0227
  resultLine "f0228" f0228
  resultLine "f0229" f0229
  resultLine "f0230" f0230
  resultLine "f0231" f0231
  resultLine "f0232" f0232
  resultLine "f0233" f0233
  resultLine "f0234" f0234
  resultLine "f0235" f0235
  resultLine "f0236" f0236
  resultLine "f0237" f0237
  resultLine "f0238" f0238
  resultLine "f0239" f0239
  resultLine "f0240" f0240
  resultLine "f0241" f0241
  resultLine "f0242" f0242
  resultLine "f0243" f0243
  resultLine "f0244" f0244
  resultLine "f0245" f0245
  resultLine "f0246" f0246
  resultLine "f0247" f0247
  resultLine "f0248" f0248
  resultLine "f0249" f0249

def runChunk5 : IO Unit := do
  resultLine "f0250" f0250
  resultLine "f0251" f0251
  resultLine "f0252" f0252
  resultLine "f0253" f0253
  resultLine "f0254" f0254
  resultLine "f0255" f0255
  resultLine "f0256" f0256
  resultLine "f0257" f0257
  resultLine "f0258" f0258
  resultLine "f0259" f0259
  resultLine "f0260" f0260
  resultLine "f0261" f0261
  resultLine "f0262" f0262
  resultLine "f0263" f0263
  resultLine "f0264" f0264
  resultLine "f0265" f0265
  resultLine "f0266" f0266
  resultLine "f0267" f0267
  resultLine "f0268" f0268
  resultLine "f0269" f0269
  resultLine "f0270" f0270
  resultLine "f0271" f0271
  resultLine "f0272" f0272
  resultLine "f0273" f0273
  resultLine "f0274" f0274
  resultLine "f0275" f0275
  resultLine "f0276" f0276
  resultLine "f0277" f0277
  resultLine "f0278" f0278
  resultLine "f0279" f0279
  resultLine "f0280" f0280
  resultLine "f0281" f0281
  resultLine "f0282" f0282
  resultLine "f0283" f0283
  resultLine "f0284" f0284
  resultLine "f0285" f0285
  resultLine "f0286" f0286
  resultLine "f0287" f0287
  resultLine "f0288" f0288
  resultLine "f0289" f0289
  resultLine "f0290" f0290
  resultLine "f0291" f0291
  resultLine "f0292" f0292
  resultLine "f0293" f0293
  resultLine "f0294" f0294
  resultLine "f0295" f0295
  resultLine "f0296" f0296
  resultLine "f0297" f0297
  resultLine "f0298" f0298
  resultLine "f0299" f0299

def runChunk6 : IO Unit := do
  resultLine "f0300" f0300
  resultLine "f0301" f0301
  resultLine "f0302" f0302
  resultLine "f0303" f0303
  resultLine "f0304" f0304
  resultLine "f0305" f0305
  resultLine "f0306" f0306
  resultLine "f0307" f0307
  resultLine "f0308" f0308
  resultLine "f0309" f0309
  resultLine "f0310" f0310
  resultLine "f0311" f0311
  resultLine "f0312" f0312
  resultLine "f0313" f0313
  resultLine "f0314" f0314
  resultLine "f0315" f0315
  resultLine "f0316" f0316
  resultLine "f0317" f0317
  resultLine "f0318" f0318
  resultLine "f0319" f0319
  resultLine "f0320" f0320
  resultLine "f0321" f0321
  resultLine "f0322" f0322
  resultLine "f0323" f0323
  resultLine "f0324" f0324
  resultLine "f0325" f0325
  resultLine "f0326" f0326
  resultLine "f0327" f0327
  resultLine "f0328" f0328
  resultLine "f0329" f0329
  resultLine "f0330" f0330
  resultLine "f0331" f0331
  resultLine "f0332" f0332
  resultLine "f0333" f0333
  resultLine "f0334" f0334
  resultLine "f0335" f0335
  resultLine "f0336" f0336
  resultLine "f0337" f0337
  resultLine "f0338" f0338
  resultLine "f0339" f0339
  resultLine "f0340" f0340
  resultLine "f0341" f0341
  resultLine "f0342" f0342
  resultLine "f0343" f0343
  resultLine "f0344" f0344
  resultLine "f0345" f0345
  resultLine "f0346" f0346
  resultLine "f0347" f0347
  resultLine "f0348" f0348
  resultLine "f0349" f0349

def runChunk7 : IO Unit := do
  resultLine "f0350" f0350
  resultLine "f0351" f0351
  resultLine "f0352" f0352
  resultLine "f0353" f0353
  resultLine "f0354" f0354
  resultLine "f0355" f0355
  resultLine "f0356" f0356
  resultLine "f0357" f0357
  resultLine "f0358" f0358
  resultLine "f0359" f0359
  resultLine "f0360" f0360
  resultLine "f0361" f0361
  resultLine "f0362" f0362
  resultLine "f0363" f0363
  resultLine "f0364" f0364
  resultLine "f0365" f0365
  resultLine "f0366" f0366
  resultLine "f0367" f0367
  resultLine "f0368" f0368
  resultLine "f0369" f0369
  resultLine "f0370" f0370
  resultLine "f0371" f0371
  resultLine "f0372" f0372
  resultLine "f0373" f0373
  resultLine "f0374" f0374
  resultLine "f0375" f0375
  resultLine "f0376" f0376
  resultLine "f0377" f0377
  resultLine "f0378" f0378
  resultLine "f0379" f0379
  resultLine "f0380" f0380
  resultLine "f0381" f0381
  resultLine "f0382" f0382
  resultLine "f0383" f0383
  resultLine "f0384" f0384
  resultLine "f0385" f0385
  resultLine "f0386" f0386
  resultLine "f0387" f0387
  resultLine "f0388" f0388
  resultLine "f0389" f0389
  resultLine "f0390" f0390
  resultLine "f0391" f0391
  resultLine "f0392" f0392
  resultLine "f0393" f0393
  resultLine "f0394" f0394
  resultLine "f0395" f0395
  resultLine "f0396" f0396
  resultLine "f0397" f0397
  resultLine "f0398" f0398
  resultLine "f0399" f0399

def runChunk8 : IO Unit := do
  resultLine "f0400" f0400
  resultLine "f0401" f0401
  resultLine "f0402" f0402
  resultLine "f0403" f0403
  resultLine "f0404" f0404
  resultLine "f0405" f0405
  resultLine "f0406" f0406
  resultLine "f0407" f0407
  resultLine "f0408" f0408
  resultLine "f0409" f0409
  resultLine "f0410" f0410
  resultLine "f0411" f0411
  resultLine "f0412" f0412
  resultLine "f0413" f0413
  resultLine "f0414" f0414
  resultLine "f0415" f0415
  resultLine "f0416" f0416
  resultLine "f0417" f0417
  resultLine "f0418" f0418
  resultLine "f0419" f0419
  resultLine "f0420" f0420
  resultLine "f0421" f0421
  resultLine "f0422" f0422
  resultLine "f0423" f0423
  resultLine "f0424" f0424
  resultLine "f0425" f0425
  resultLine "f0426" f0426
  resultLine "f0427" f0427
  resultLine "f0428" f0428
  resultLine "f0429" f0429
  resultLine "f0430" f0430
  resultLine "f0431" f0431
  resultLine "f0432" f0432
  resultLine "f0433" f0433
  resultLine "f0434" f0434
  resultLine "f0435" f0435
  resultLine "f0436" f0436
  resultLine "f0437" f0437
  resultLine "f0438" f0438
  resultLine "f0439" f0439
  resultLine "f0440" f0440
  resultLine "f0441" f0441
  resultLine "f0442" f0442
  resultLine "f0443" f0443
  resultLine "f0444" f0444
  resultLine "f0445" f0445
  resultLine "f0446" f0446
  resultLine "f0447" f0447
  resultLine "f0448" f0448
  resultLine "f0449" f0449

def runChunk9 : IO Unit := do
  resultLine "f0450" f0450
  resultLine "f0451" f0451
  resultLine "f0452" f0452
  resultLine "f0453" f0453
  resultLine "f0454" f0454
  resultLine "f0455" f0455
  resultLine "f0456" f0456
  resultLine "f0457" f0457
  resultLine "f0458" f0458
  resultLine "f0459" f0459
  resultLine "f0460" f0460
  resultLine "f0461" f0461
  resultLine "f0462" f0462
  resultLine "f0463" f0463
  resultLine "f0464" f0464
  resultLine "f0465" f0465
  resultLine "f0466" f0466
  resultLine "f0467" f0467
  resultLine "f0468" f0468
  resultLine "f0469" f0469
  resultLine "f0470" f0470
  resultLine "f0471" f0471
  resultLine "f0472" f0472
  resultLine "f0473" f0473
  resultLine "f0474" f0474
  resultLine "f0475" f0475
  resultLine "f0476" f0476
  resultLine "f0477" f0477
  resultLine "f0478" f0478
  resultLine "f0479" f0479
  resultLine "f0480" f0480
  resultLine "f0481" f0481
  resultLine "f0482" f0482
  resultLine "f0483" f0483
  resultLine "f0484" f0484
  resultLine "f0485" f0485
  resultLine "f0486" f0486
  resultLine "f0487" f0487
  resultLine "f0488" f0488
  resultLine "f0489" f0489
  resultLine "f0490" f0490
  resultLine "f0491" f0491
  resultLine "f0492" f0492
  resultLine "f0493" f0493
  resultLine "f0494" f0494
  resultLine "f0495" f0495
  resultLine "f0496" f0496
  resultLine "f0497" f0497
  resultLine "f0498" f0498
  resultLine "f0499" f0499

def runChunk10 : IO Unit := do
  resultLine "f0500" f0500
  resultLine "f0501" f0501
  resultLine "f0502" f0502
  resultLine "f0503" f0503
  resultLine "f0504" f0504
  resultLine "f0505" f0505
  resultLine "f0506" f0506
  resultLine "f0507" f0507
  resultLine "f0508" f0508
  resultLine "f0509" f0509
  resultLine "f0510" f0510
  resultLine "f0511" f0511
  resultLine "f0512" f0512
  resultLine "f0513" f0513
  resultLine "f0514" f0514
  resultLine "f0515" f0515
  resultLine "f0516" f0516
  resultLine "f0517" f0517
  resultLine "f0518" f0518
  resultLine "f0519" f0519
  resultLine "f0520" f0520
  resultLine "f0521" f0521
  resultLine "f0522" f0522
  resultLine "f0523" f0523
  resultLine "f0524" f0524
  resultLine "f0525" f0525
  resultLine "f0526" f0526
  resultLine "f0527" f0527
  resultLine "f0528" f0528
  resultLine "f0529" f0529
  resultLine "f0530" f0530
  resultLine "f0531" f0531
  resultLine "f0532" f0532
  resultLine "f0533" f0533
  resultLine "f0534" f0534
  resultLine "f0535" f0535
  resultLine "f0536" f0536
  resultLine "f0537" f0537
  resultLine "f0538" f0538
  resultLine "f0539" f0539
  resultLine "f0540" f0540
  resultLine "f0541" f0541
  resultLine "f0542" f0542
  resultLine "f0543" f0543
  resultLine "f0544" f0544
  resultLine "f0545" f0545
  resultLine "f0546" f0546
  resultLine "f0547" f0547
  resultLine "f0548" f0548
  resultLine "f0549" f0549

def runChunk11 : IO Unit := do
  resultLine "f0550" f0550
  resultLine "f0551" f0551
  resultLine "f0552" f0552
  resultLine "f0553" f0553
  resultLine "f0554" f0554
  resultLine "f0555" f0555
  resultLine "f0556" f0556
  resultLine "f0557" f0557
  resultLine "f0558" f0558
  resultLine "f0559" f0559
  resultLine "f0560" f0560
  resultLine "f0561" f0561
  resultLine "f0562" f0562
  resultLine "f0563" f0563
  resultLine "f0564" f0564
  resultLine "f0565" f0565
  resultLine "f0566" f0566
  resultLine "f0567" f0567
  resultLine "f0568" f0568
  resultLine "f0569" f0569
  resultLine "f0570" f0570
  resultLine "f0571" f0571
  resultLine "f0572" f0572
  resultLine "f0573" f0573
  resultLine "f0574" f0574
  resultLine "f0575" f0575
  resultLine "f0576" f0576
  resultLine "f0577" f0577
  resultLine "f0578" f0578
  resultLine "f0579" f0579
  resultLine "f0580" f0580
  resultLine "f0581" f0581
  resultLine "f0582" f0582
  resultLine "f0583" f0583
  resultLine "f0584" f0584
  resultLine "f0585" f0585
  resultLine "f0586" f0586
  resultLine "f0587" f0587
  resultLine "f0588" f0588
  resultLine "f0589" f0589
  resultLine "f0590" f0590
  resultLine "f0591" f0591
  resultLine "f0592" f0592
  resultLine "f0593" f0593
  resultLine "f0594" f0594
  resultLine "f0595" f0595
  resultLine "f0596" f0596
  resultLine "f0597" f0597
  resultLine "f0598" f0598
  resultLine "f0599" f0599

def runChunk12 : IO Unit := do
  resultLine "f0600" f0600
  resultLine "f0601" f0601
  resultLine "f0602" f0602
  resultLine "f0603" f0603
  resultLine "f0604" f0604
  resultLine "f0605" f0605
  resultLine "f0606" f0606
  resultLine "f0607" f0607
  resultLine "f0608" f0608
  resultLine "f0609" f0609
  resultLine "f0610" f0610
  resultLine "f0611" f0611
  resultLine "f0612" f0612
  resultLine "f0613" f0613
  resultLine "f0614" f0614
  resultLine "f0615" f0615
  resultLine "f0616" f0616
  resultLine "f0617" f0617
  resultLine "f0618" f0618
  resultLine "f0619" f0619
  resultLine "f0620" f0620
  resultLine "f0621" f0621
  resultLine "f0622" f0622
  resultLine "f0623" f0623
  resultLine "f0624" f0624
  resultLine "f0625" f0625
  resultLine "f0626" f0626
  resultLine "f0627" f0627
  resultLine "f0628" f0628
  resultLine "f0629" f0629
  resultLine "f0630" f0630
  resultLine "f0631" f0631
  resultLine "f0632" f0632
  resultLine "f0633" f0633
  resultLine "f0634" f0634
  resultLine "f0635" f0635
  resultLine "f0636" f0636
  resultLine "f0637" f0637
  resultLine "f0638" f0638
  resultLine "f0639" f0639
  resultLine "f0640" f0640
  resultLine "f0641" f0641
  resultLine "f0642" f0642
  resultLine "f0643" f0643
  resultLine "f0644" f0644
  resultLine "f0645" f0645
  resultLine "f0646" f0646
  resultLine "f0647" f0647
  resultLine "f0648" f0648
  resultLine "f0649" f0649

def runChunk13 : IO Unit := do
  resultLine "f0650" f0650
  resultLine "f0651" f0651
  resultLine "f0652" f0652
  resultLine "f0653" f0653
  resultLine "f0654" f0654
  resultLine "f0655" f0655
  resultLine "f0656" f0656
  resultLine "f0657" f0657
  resultLine "f0658" f0658
  resultLine "f0659" f0659
  resultLine "f0660" f0660
  resultLine "f0661" f0661
  resultLine "f0662" f0662
  resultLine "f0663" f0663
  resultLine "f0664" f0664
  resultLine "f0665" f0665
  resultLine "f0666" f0666
  resultLine "f0667" f0667
  resultLine "f0668" f0668
  resultLine "f0669" f0669
  resultLine "f0670" f0670
  resultLine "f0671" f0671
  resultLine "f0672" f0672
  resultLine "f0673" f0673
  resultLine "f0674" f0674
  resultLine "f0675" f0675
  resultLine "f0676" f0676
  resultLine "f0677" f0677
  resultLine "f0678" f0678
  resultLine "f0679" f0679
  resultLine "f0680" f0680
  resultLine "f0681" f0681
  resultLine "f0682" f0682
  resultLine "f0683" f0683
  resultLine "f0684" f0684
  resultLine "f0685" f0685
  resultLine "f0686" f0686
  resultLine "f0687" f0687
  resultLine "f0688" f0688
  resultLine "f0689" f0689
  resultLine "f0690" f0690
  resultLine "f0691" f0691
  resultLine "f0692" f0692
  resultLine "f0693" f0693
  resultLine "f0694" f0694
  resultLine "f0695" f0695
  resultLine "f0696" f0696
  resultLine "f0697" f0697
  resultLine "f0698" f0698
  resultLine "f0699" f0699

def runChunk14 : IO Unit := do
  resultLine "f0700" f0700
  resultLine "f0701" f0701
  resultLine "f0702" f0702
  resultLine "f0703" f0703
  resultLine "f0704" f0704
  resultLine "f0705" f0705
  resultLine "f0706" f0706
  resultLine "f0707" f0707
  resultLine "f0708" f0708
  resultLine "f0709" f0709
  resultLine "f0710" f0710
  resultLine "f0711" f0711
  resultLine "f0712" f0712
  resultLine "f0713" f0713
  resultLine "f0714" f0714
  resultLine "f0715" f0715
  resultLine "f0716" f0716
  resultLine "f0717" f0717
  resultLine "f0718" f0718
  resultLine "f0719" f0719
  resultLine "f0720" f0720
  resultLine "f0721" f0721
  resultLine "f0722" f0722
  resultLine "f0723" f0723
  resultLine "f0724" f0724
  resultLine "f0725" f0725
  resultLine "f0726" f0726
  resultLine "f0727" f0727
  resultLine "f0728" f0728
  resultLine "f0729" f0729
  resultLine "f0730" f0730
  resultLine "f0731" f0731
  resultLine "f0732" f0732
  resultLine "f0733" f0733
  resultLine "f0734" f0734
  resultLine "f0735" f0735
  resultLine "f0736" f0736
  resultLine "f0737" f0737
  resultLine "f0738" f0738
  resultLine "f0739" f0739
  resultLine "f0740" f0740
  resultLine "f0741" f0741
  resultLine "f0742" f0742
  resultLine "f0743" f0743
  resultLine "f0744" f0744
  resultLine "f0745" f0745
  resultLine "f0746" f0746
  resultLine "f0747" f0747
  resultLine "f0748" f0748
  resultLine "f0749" f0749

def runChunk15 : IO Unit := do
  resultLine "f0750" f0750
  resultLine "f0751" f0751
  resultLine "f0752" f0752
  resultLine "f0753" f0753
  resultLine "f0754" f0754
  resultLine "f0755" f0755
  resultLine "f0756" f0756
  resultLine "f0757" f0757
  resultLine "f0758" f0758
  resultLine "f0759" f0759
  resultLine "f0760" f0760
  resultLine "f0761" f0761
  resultLine "f0762" f0762
  resultLine "f0763" f0763
  resultLine "f0764" f0764
  resultLine "f0765" f0765
  resultLine "f0766" f0766
  resultLine "f0767" f0767
  resultLine "f0768" f0768
  resultLine "f0769" f0769
  resultLine "f0770" f0770
  resultLine "f0771" f0771
  resultLine "f0772" f0772
  resultLine "f0773" f0773
  resultLine "f0774" f0774
  resultLine "f0775" f0775
  resultLine "f0776" f0776
  resultLine "f0777" f0777
  resultLine "f0778" f0778
  resultLine "f0779" f0779
  resultLine "f0780" f0780
  resultLine "f0781" f0781
  resultLine "f0782" f0782
  resultLine "f0783" f0783
  resultLine "f0784" f0784
  resultLine "f0785" f0785
  resultLine "f0786" f0786
  resultLine "f0787" f0787
  resultLine "f0788" f0788
  resultLine "f0789" f0789
  resultLine "f0790" f0790
  resultLine "f0791" f0791
  resultLine "f0792" f0792
  resultLine "f0793" f0793
  resultLine "f0794" f0794
  resultLine "f0795" f0795
  resultLine "f0796" f0796
  resultLine "f0797" f0797
  resultLine "f0798" f0798
  resultLine "f0799" f0799

def runChunk16 : IO Unit := do
  resultLine "f0800" f0800
  resultLine "f0801" f0801
  resultLine "f0802" f0802
  resultLine "f0803" f0803
  resultLine "f0804" f0804
  resultLine "f0805" f0805
  resultLine "f0806" f0806
  resultLine "f0807" f0807
  resultLine "f0808" f0808
  resultLine "f0809" f0809
  resultLine "f0810" f0810
  resultLine "f0811" f0811
  resultLine "f0812" f0812
  resultLine "f0813" f0813
  resultLine "f0814" f0814
  resultLine "f0815" f0815
  resultLine "f0816" f0816
  resultLine "f0817" f0817
  resultLine "f0818" f0818
  resultLine "f0819" f0819
  resultLine "f0820" f0820
  resultLine "f0821" f0821
  resultLine "f0822" f0822
  resultLine "f0823" f0823
  resultLine "f0824" f0824
  resultLine "f0825" f0825
  resultLine "f0826" f0826
  resultLine "f0827" f0827
  resultLine "f0828" f0828
  resultLine "f0829" f0829
  resultLine "f0830" f0830
  resultLine "f0831" f0831
  resultLine "f0832" f0832
  resultLine "f0833" f0833
  resultLine "f0834" f0834
  resultLine "f0835" f0835
  resultLine "f0836" f0836
  resultLine "f0837" f0837
  resultLine "f0838" f0838
  resultLine "f0839" f0839
  resultLine "f0840" f0840
  resultLine "f0841" f0841
  resultLine "f0842" f0842
  resultLine "f0843" f0843
  resultLine "f0844" f0844
  resultLine "f0845" f0845
  resultLine "f0846" f0846
  resultLine "f0847" f0847
  resultLine "f0848" f0848
  resultLine "f0849" f0849

def runChunk17 : IO Unit := do
  resultLine "f0850" f0850
  resultLine "f0851" f0851
  resultLine "f0852" f0852
  resultLine "f0853" f0853
  resultLine "f0854" f0854
  resultLine "f0855" f0855
  resultLine "f0856" f0856
  resultLine "f0857" f0857
  resultLine "f0858" f0858
  resultLine "f0859" f0859
  resultLine "f0860" f0860
  resultLine "f0861" f0861
  resultLine "f0862" f0862
  resultLine "f0863" f0863
  resultLine "f0864" f0864
  resultLine "f0865" f0865
  resultLine "f0866" f0866
  resultLine "f0867" f0867
  resultLine "f0868" f0868
  resultLine "f0869" f0869
  resultLine "f0870" f0870
  resultLine "f0871" f0871
  resultLine "f0872" f0872
  resultLine "f0873" f0873
  resultLine "f0874" f0874
  resultLine "f0875" f0875
  resultLine "f0876" f0876
  resultLine "f0877" f0877
  resultLine "f0878" f0878
  resultLine "f0879" f0879
  resultLine "f0880" f0880
  resultLine "f0881" f0881
  resultLine "f0882" f0882
  resultLine "f0883" f0883
  resultLine "f0884" f0884
  resultLine "f0885" f0885
  resultLine "f0886" f0886
  resultLine "f0887" f0887
  resultLine "f0888" f0888
  resultLine "f0889" f0889
  resultLine "f0890" f0890
  resultLine "f0891" f0891
  resultLine "f0892" f0892
  resultLine "f0893" f0893
  resultLine "f0894" f0894
  resultLine "f0895" f0895
  resultLine "f0896" f0896
  resultLine "f0897" f0897
  resultLine "f0898" f0898
  resultLine "f0899" f0899

def runChunk18 : IO Unit := do
  resultLine "f0900" f0900
  resultLine "f0901" f0901
  resultLine "f0902" f0902
  resultLine "f0903" f0903
  resultLine "f0904" f0904
  resultLine "f0905" f0905
  resultLine "f0906" f0906
  resultLine "f0907" f0907
  resultLine "f0908" f0908
  resultLine "f0909" f0909
  resultLine "f0910" f0910
  resultLine "f0911" f0911
  resultLine "f0912" f0912
  resultLine "f0913" f0913
  resultLine "f0914" f0914
  resultLine "f0915" f0915
  resultLine "f0916" f0916
  resultLine "f0917" f0917
  resultLine "f0918" f0918
  resultLine "f0919" f0919
  resultLine "f0920" f0920
  resultLine "f0921" f0921
  resultLine "f0922" f0922
  resultLine "f0923" f0923
  resultLine "f0924" f0924
  resultLine "f0925" f0925
  resultLine "f0926" f0926
  resultLine "f0927" f0927
  resultLine "f0928" f0928
  resultLine "f0929" f0929
  resultLine "f0930" f0930
  resultLine "f0931" f0931
  resultLine "f0932" f0932
  resultLine "f0933" f0933
  resultLine "f0934" f0934
  resultLine "f0935" f0935
  resultLine "f0936" f0936
  resultLine "f0937" f0937
  resultLine "f0938" f0938
  resultLine "f0939" f0939
  resultLine "f0940" f0940
  resultLine "f0941" f0941
  resultLine "f0942" f0942
  resultLine "f0943" f0943
  resultLine "f0944" f0944
  resultLine "f0945" f0945
  resultLine "f0946" f0946
  resultLine "f0947" f0947
  resultLine "f0948" f0948
  resultLine "f0949" f0949

def runChunk19 : IO Unit := do
  resultLine "f0950" f0950
  resultLine "f0951" f0951
  resultLine "f0952" f0952
  resultLine "f0953" f0953
  resultLine "f0954" f0954
  resultLine "f0955" f0955
  resultLine "f0956" f0956
  resultLine "f0957" f0957
  resultLine "f0958" f0958
  resultLine "f0959" f0959
  resultLine "f0960" f0960
  resultLine "f0961" f0961
  resultLine "f0962" f0962
  resultLine "f0963" f0963
  resultLine "f0964" f0964
  resultLine "f0965" f0965
  resultLine "f0966" f0966
  resultLine "f0967" f0967
  resultLine "f0968" f0968
  resultLine "f0969" f0969
  resultLine "f0970" f0970
  resultLine "f0971" f0971
  resultLine "f0972" f0972
  resultLine "f0973" f0973
  resultLine "f0974" f0974
  resultLine "f0975" f0975
  resultLine "f0976" f0976
  resultLine "f0977" f0977
  resultLine "f0978" f0978
  resultLine "f0979" f0979
  resultLine "f0980" f0980
  resultLine "f0981" f0981
  resultLine "f0982" f0982
  resultLine "f0983" f0983
  resultLine "f0984" f0984
  resultLine "f0985" f0985
  resultLine "f0986" f0986
  resultLine "f0987" f0987
  resultLine "f0988" f0988
  resultLine "f0989" f0989
  resultLine "f0990" f0990
  resultLine "f0991" f0991
  resultLine "f0992" f0992
  resultLine "f0993" f0993
  resultLine "f0994" f0994
  resultLine "f0995" f0995
  resultLine "f0996" f0996
  resultLine "f0997" f0997
  resultLine "f0998" f0998
  resultLine "f0999" f0999

def runChunk20 : IO Unit := do
  resultLine "f1000" f1000
  resultLine "f1001" f1001
  resultLine "f1002" f1002
  resultLine "f1003" f1003
  resultLine "f1004" f1004
  resultLine "f1005" f1005
  resultLine "f1006" f1006
  resultLine "f1007" f1007
  resultLine "f1008" f1008
  resultLine "f1009" f1009
  resultLine "f1010" f1010
  resultLine "f1011" f1011
  resultLine "f1012" f1012
  resultLine "f1013" f1013
  resultLine "f1014" f1014
  resultLine "f1015" f1015
  resultLine "f1016" f1016
  resultLine "f1017" f1017
  resultLine "f1018" f1018
  resultLine "f1019" f1019
  resultLine "f1020" f1020
  resultLine "f1021" f1021
  resultLine "f1022" f1022
  resultLine "f1023" f1023
  resultLine "f1024" f1024
  resultLine "f1025" f1025
  resultLine "f1026" f1026
  resultLine "f1027" f1027
  resultLine "f1028" f1028
  resultLine "f1029" f1029
  resultLine "f1030" f1030
  resultLine "f1031" f1031
  resultLine "f1032" f1032
  resultLine "f1033" f1033
  resultLine "f1034" f1034
  resultLine "f1035" f1035
  resultLine "f1036" f1036
  resultLine "f1037" f1037
  resultLine "f1038" f1038
  resultLine "f1039" f1039
  resultLine "f1040" f1040
  resultLine "f1041" f1041
  resultLine "f1042" f1042
  resultLine "f1043" f1043
  resultLine "f1044" f1044
  resultLine "f1045" f1045
  resultLine "f1046" f1046
  resultLine "f1047" f1047
  resultLine "f1048" f1048
  resultLine "f1049" f1049

def runChunk21 : IO Unit := do
  resultLine "f1050" f1050
  resultLine "f1051" f1051
  resultLine "f1052" f1052
  resultLine "f1053" f1053
  resultLine "f1054" f1054
  resultLine "f1055" f1055
  resultLine "f1056" f1056
  resultLine "f1057" f1057
  resultLine "f1058" f1058
  resultLine "f1059" f1059
  resultLine "f1060" f1060
  resultLine "f1061" f1061
  resultLine "f1062" f1062
  resultLine "f1063" f1063
  resultLine "f1064" f1064
  resultLine "f1065" f1065
  resultLine "f1066" f1066
  resultLine "f1067" f1067
  resultLine "f1068" f1068
  resultLine "f1069" f1069
  resultLine "f1070" f1070
  resultLine "f1071" f1071
  resultLine "f1072" f1072

def main : IO Unit := do
  runChunk0
  runChunk1
  runChunk2
  runChunk3
  runChunk4
  runChunk5
  runChunk6
  runChunk7
  runChunk8
  runChunk9
  runChunk10
  runChunk11
  runChunk12
  runChunk13
  runChunk14
  runChunk15
  runChunk16
  runChunk17
  runChunk18
  runChunk19
  runChunk20
  runChunk21
  resultLine "m_order_correct" (.eq (.var 1) (.zero : Term 2))
  resultLine "m_order_mutant" (.eq (.var 0) (.zero : Term 2))
  resultLine "m_shadow_correct" (.ex (.neg (.eq (.var 0) (.zero : Term 2))))
  resultLine "m_shadow_mutant" (.ex (.neg (.eq (.var 1) (.zero : Term 2))))
  refinementLine 0 1
  refinementLine 1 1
  refinementLine 1 2
  refinementLine 1 3
  refinementLine 2 1
  refinementLine 2 2
  refinementLine 2 3
  refinementLine 2 4
  refinementLine 2 5
  refinementLine 2 6
  refinementLine 2 7
  refinementLine 2 8
  refinementLine 2 9
  refinementLine 2 10
  refinementLine 2 11
  refinementLine 2 12
  refinementLine 2 13
  refinementLine 2 14
  refinementLine 2 15
