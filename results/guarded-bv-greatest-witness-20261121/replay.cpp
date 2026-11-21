#include "guarded_bv.hpp"
#include <iostream>
#include <stdexcept>

using guarded_bv::Bits;
using guarded_bv::Clause;
using guarded_bv::NonzeroTerm;
using guarded_bv::greatest_witness;
using Word = std::uint64_t;

static void check(bool ok, const char* message) {
    if (!ok) throw std::logic_error(message);
}

static Clause clause(unsigned w, Word u, Word v,
                     NonzeroTerm term = NonzeroTerm::x_and_v) {
    return {{w, u}, {w, v}, term};
}

// Evaluate the original mixed-sign formula directly for a given assignment.
static bool direct(Word x, Word y, const std::vector<Clause>& cs) {
    if ((x & y) != 0) return false;
    for (const auto& c : cs) {
        const Word tested = c.nonzero_term == NonzeroTerm::complement_x_and_v ? ~x : x;
        if ((x & c.u.value) != 0 && (tested & c.v.value) == 0) return false;
    }
    return true;
}

static void exhaust(unsigned n) {
    unsigned schedules = 1;
    for (unsigned i = 0; i < n; ++i) schedules *= 16;
    unsigned instances = 0, assignments = 0, nonzero = 0;
    for (unsigned code = 0; code < schedules; ++code) {
        std::vector<Clause> cs;
        auto digits = code;
        for (unsigned i = 0; i < n; ++i) {
            cs.push_back(clause(2, digits % 4, (digits / 4) % 4));
            digits /= 16;
        }
        for (Word y = 0; y < 4; ++y) {
            const auto result = greatest_witness({2,y}, cs);
            check(result.has_value(), "supported case deferred");
            Word joined = 0;
            for (Word x = 0; x < 4; ++x) {
                if (direct(x,y,cs)) joined |= x;
                ++assignments;
            }
            check(direct(result->greatest,y,cs), "greatest value infeasible");
            check(joined == result->greatest, "lost feasible value");
            check(result->admits_nonzero() == (joined != 0), "wrong existential answer");
            nonzero += result->admits_nonzero();
            ++instances;
        }
    }
    std::cout << "width=2 clauses=" << n << " schedules=" << schedules
              << " instances=" << instances << " assignments=" << assignments
              << " nonzero_sat=" << nonzero << '\n';
}

int main() {
    for (unsigned n = 1; n <= 3; ++n) exhaust(n);
    const auto high = Word{1} << 63;
    const auto top = std::numeric_limits<Word>::max();
    check(greatest_witness({64,0},{}).value().greatest == top, "full-width complement");
    check(greatest_witness({64,top ^ high},{}).value().greatest == high, "top bit");
    check(greatest_witness({64,0},{clause(64,high,0)}).value().greatest == (top ^ high),
          "top-bit elimination");
    check(greatest_witness({64,top},{}).value().greatest == 0, "zero-only result");
    check(greatest_witness({4,0},{clause(4,4,2),clause(4,2,1),clause(4,1,0)}).value().greatest == 8,
          "later clause must re-enable an earlier reduction");
    check(!greatest_witness({0,0},{}), "zero width");
    check(!greatest_witness({65,0},{}), "width above 64");
    check(!greatest_witness({2,4},{}), "guard out of range");
    check(!greatest_witness({2,0},{{{2,1},{3,1}}}), "mixed width");
    check(!greatest_witness({2,0},{clause(2,4,1)}), "coefficient out of range");
    check(!greatest_witness({2,0},{clause(2,1,1,NonzeroTerm::unsupported)}), "unsupported term");
    // Anti-control: (~x & 2) != 0. Solutions 1 and 2 have invalid join 3.
    const std::vector<Clause> anti{clause(2,1,2,NonzeroTerm::complement_x_and_v)};
    check(direct(1,0,anti) && direct(2,0,anti) && !direct(3,0,anti), "polarity control");
    check(!greatest_witness({2,0},anti), "wrong polarity must defer");
    std::cout << "width64=pass cascade=8 malformed_inputs=deferred "
                 "complemented_x_control=deferred feasible_1_and_2_infeasible_join_3=true\n";
}
