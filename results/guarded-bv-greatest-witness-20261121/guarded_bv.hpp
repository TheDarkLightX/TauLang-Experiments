#ifndef TAU_EXAMPLE_GUARDED_BV_HPP
#define TAU_EXAMPLE_GUARDED_BV_HPP

#include <algorithm>
#include <cstdint>
#include <limits>
#include <optional>
#include <vector>

namespace guarded_bv {

// The caller extracts this fragment from its typed AST. The width is the
// declared bit-vector width. Values must be concrete, canonical bit patterns.
struct Bits {
    unsigned width;
    std::uint64_t value;
};

enum class NonzeroTerm { x_and_v, complement_x_and_v, unsupported };

struct Clause {
    Bits u;
    Bits v;
    NonzeroTerm nonzero_term = NonzeroTerm::x_and_v;
};

struct Result {
    std::uint64_t greatest;
    bool admits_nonzero() const { return greatest != 0; }
};

// For x & y = 0 and each ((x & u) = 0 or (x & v) != 0), compute the
// greatest solution under bitwise inclusion. nullopt asks the caller to
// retain its existing path. A present result with greatest == 0 is valid.
// This API assumes the same bound x in every recognized operand.
inline std::optional<Result> greatest_witness(Bits y, const std::vector<Clause>& clauses) {
    if (y.width == 0 || y.width > 64) return std::nullopt;
    const auto top = y.width == 64 ? std::numeric_limits<std::uint64_t>::max()
                                  : (std::uint64_t{1} << y.width) - 1;
    const auto valid = [&](Bits t) { return t.width == y.width && (t.value & ~top) == 0; };
    if (!valid(y)) return std::nullopt;
    for (const auto& c : clauses) {
        if (c.nonzero_term != NonzeroTerm::x_and_v || !valid(c.u) || !valid(c.v))
            return std::nullopt;
    }

    auto bound = top ^ y.value;
    auto pending = clauses;
    while (!pending.empty()) {
        const auto forced = std::find_if(pending.begin(), pending.end(),
            [&](const Clause& c) { return (bound & c.v.value) == 0; });
        if (forced == pending.end()) break;
        bound &= ~forced->u.value;
        pending.erase(forced); // Every later bound continues to avoid this u.
    }
    return Result{bound};
}

} // namespace guarded_bv
#endif
