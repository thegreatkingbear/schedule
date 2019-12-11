from __future__ import print_function
from ortools.sat.python import cp_model

class MembersPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, shiftsA, shiftsB, num_members, num_days, num_shifts, sols):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._shiftsA = shiftsA
        self._shiftsB = shiftsB
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
                        if self.Value(self._shiftsA[(n, d, s)]):
                            is_working = True
                            print('  Member %i works shiftA %i' % (n, s))
                        if self.Value(self._shiftsB[(n, d, s)]):
                            is_working = True
                            print('  Member %i works shiftB %i' % (n, s))
                    if not is_working:
                        print('  Member {} does not work'.format(n))
            print()
        self._solution_count += 1

    def solution_count(self):
        return self._solution_count

def main():
    names = ['박호원', '이보람', '정형섭', '남영선', '양혜경', '이찬희', '이장훈', '조인경']
    # names = ['박호원', '이보람', '정형섭']
    num_days = 31
    num_shiftsA = 1
    num_shiftsB = 1
    num_members = len(names)

    all_members = range(num_members)
    all_shiftsA = range(num_shiftsA)
    all_shiftsB = range(num_shiftsB)
    num_shifts = num_shiftsA + num_shiftsB
    all_shifts = range(num_shifts)
    all_days = range(num_days)

    model = cp_model.CpModel()
    shiftsA = {}
    shiftsB = {}
    for n in all_members:
        for d in all_days:
            shiftsA[(n, d, 0)] = model.NewBoolVar('shiftA_n%id%is%i' % (n, d, 0))
            shiftsB[(n, d, 0)] = model.NewBoolVar('shiftB_n%id%is%i' % (n, d, 0))
            print('shiftA_n%id%is%i' % (n, d, 0))
            print(shiftsA[(n, d, 0)].Name())
            print('shiftB_n%id%is%i' % (n, d, 0))
            print(shiftsB[(n, d, 0)].DebugString())

    for d in all_days:
        for a in all_shiftsA:
            model.Add(sum(shiftsA[(n, d, a)] for n in all_members) == 1)
        for b in all_shiftsB:
            model.Add(sum(shiftsB[(n, d, b)] for n in all_members) == 1)

    for n in all_members:
        for d in all_days:
            model.Add(sum(shiftsA[(n, d, a)] for a in all_shiftsA) <= 1)
            model.Add(sum(shiftsB[(n, d, b)] for b in all_shiftsB) <= 1)
            model.Add( not (shiftsA[(n, d, 0)] == 1 and shiftsB[(n, d, 0)] == 1))

    # min_shifts_per_member is the largest integer such that every nurse
    # can be assigned at least that many shifts. If the number of nurses doesn't
    # divide the total number of shifts over the schedule period,
    # some nurses have to work one more shift, for a total of
    # min_shifts_per_member + 1.
    min_shiftsA_per_member = (num_shiftsA * num_days) // num_members
    min_shiftsB_per_member = (num_shiftsB * num_days) // num_members
    print("min_shifts_per_member", min_shiftsA_per_member)
    max_shiftsA_per_member = min_shiftsA_per_member + 1
    max_shiftsB_per_member = min_shiftsB_per_member + 1
    for n in all_members:
        num_shiftsA_worked = sum(shiftsA[(n, d, 0)] for d in all_days)
        num_shiftsB_worked = sum(shiftsB[(n, d, 0)] for d in all_days)
        model.Add(min_shiftsA_per_member <= num_shiftsA_worked)
        model.Add(min_shiftsB_per_member <= num_shiftsB_worked)
        model.Add(num_shiftsA_worked <= max_shiftsA_per_member)
        model.Add(num_shiftsB_worked <= max_shiftsB_per_member)

    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 0
    a_few_solutions = range(5)
    solution_printer = MembersPartialSolutionPrinter(shiftsA, shiftsB, num_members, num_days, num_shifts, a_few_solutions)
    solver.SearchForAllSolutions(model, solution_printer)

    print()
    print('Statistics')
    print(' - conflicts             : %i' % solver.NumConflicts())
    print(' - branches              : %i' % solver.NumBranches())
    print(' - wall time             : %f s' % solver.WallTime())
    print(' - solutions found       : %i' % solution_printer.solution_count())

if __name__ == '__main__':
    main()