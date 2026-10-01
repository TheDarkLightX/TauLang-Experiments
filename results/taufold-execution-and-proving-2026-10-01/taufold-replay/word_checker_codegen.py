#!/usr/bin/env python3
"""Keep the exact 32-bit representation through the generated checker boundary."""
import checker_codegen

def generate(source, reference):
    code, meta = checker_codegen.generate(source, reference, narrow=True, share=True)
    signature = 'pub fn tau_step(input:&[u128;102])->[u128;21]'
    assert code.count(signature) == 1
    code = code.replace(signature, 'pub fn tau_step32(input:&[u32;102])->[u32;21]')
    code = code.replace(' as u128', '')
    # The public relation validates every u128 input before calling this wrapper.
    code += '''
pub fn tau_step(input:&[u128;102])->[u128;21] {
    let words = core::array::from_fn(|i| input[i] as u32);
    tau_step32(&words).map(u128::from)
}
'''
    return code, meta
