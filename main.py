from __future__ import print_function
from ortools.sat.python import cp_model

class MembersPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, shifts, num_members, num_days, num_shifts, sols):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._shifts = shifts
        self._num_members = num_members
        self._num_days = num_days
        self._num_shifts = num_shifts
        self._solutions = set(sols)
        self._solution_count = 0

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            print('Solution %i' % self._solution_count)
            for d in range(self._num_days):
                print('Day %i' % d)
                for n in range(self._num_members):
                    is_working = False
                    for s in range(self._num_shifts):
                        if self.Value(self._shifts[(n, d, s)]):
                            is_working = True
                            print('  Nurse %i works shift %i' % (n, s))
                    if not is_working:
                        print('  Member {} does not work'.format(n))
            print()
        self._solution_count += 1

    def solution_count(self):
        return self._solution_count

def main():
    names = ['박호원', '이보람', '정형섭', '남영선', '양혜경', '이찬희', '이장훈', '조인경']
    num_days = 31
    num_shifts = 2
    num_members = len(names)

    all_members = range(num_members)
    all_shifts = range(num_shifts)
    all_days = range(num_days)

    CONST_X = 10
    MIN_A = 2
    MAX_A = 2
    stack_x = [10, 10, 10, 10, 10, 10, 10, 10]

    model = cp_model.CpModel()
    shifts = {}
    for n in all_members:
        for d in all_days:
            for s in all_shifts:
                shifts[(n, d, s)] = model.NewBoolVar('shift_n%id%is%i' % (n, d, s))

    for d in all_days:
        for s in all_shifts:
            model.Add(sum(shifts[(n, d, s)] for n in all_members) == 2)

    for n in all_members:
        for d in all_days:
            model.Add(sum(shifts[(n, d, s)] for s in all_shifts) <= 1)

    # min_shifts_per_member is the largest integer such that every nurse
    # can be assigned at least that many shifts. If the number of nurses doesn't
    # divide the total number of shifts over the schedule period,
    # some nurses have to work one more shift, for a total of
    # min_shifts_per_member + 1.
    min_shifts_per_member = (num_shifts * num_days) // num_members
    max_shifts_per_member = min_shifts_per_member + 3
    for n in all_members:
        num_shifts_worked = sum(shifts[(n, d, s)] for d in all_days for s in all_shifts)
        model.Add(min_shifts_per_member <= num_shifts_worked)
        model.Add(num_shifts_worked <= max_shifts_per_member)

    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 0
    a_few_solutions = range(5)
    solution_printer = MembersPartialSolutionPrinter(shifts, num_members, num_days, num_shifts, a_few_solutions)
    solver.SearchForAllSolutions(model, solution_printer)

    print()
    print('Statistics')
    print(' - conflicts             : %i' % solver.NumConflicts())
    print(' - branches              : %i' % solver.NumBranches())
    print(' - wall time             : %f s' % solver.WallTime())
    print(' - solutions ffound      : %i' % solution_printer.solution_count())

if __name__ == '__main__':
    main()