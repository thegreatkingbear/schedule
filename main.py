from __future__ import print_function
from ortools.sat.python import cp_model
import csv

names = ['박호원', '이보람', '정형섭', '남영선', '양혜경', '이찬희', '이장훈', '조인경']
veterans = ['박호원', '이보람', '정형섭', '남영선', '양혜경', '이찬희']
novice = ['이장훈', '조인경']

class MembersPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, shiftsA, shiftsP, num_members, num_days, sols, names):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._shiftsA = shiftsA
        self._shiftsP = shiftsP
        self._num_members = num_members
        self._num_days = num_days
        self._solutions = set(sols)
        self._solution_count = 0
        self._names = names

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            print('Solution %i' % self._solution_count)
            with open('employee_file{}.csv'.format(self._solution_count), mode='w') as employee_file:
                employee_writer = csv.writer(
                    employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL
                )
                days = list(range(1, self._num_days + 1))
                days.insert(0, ' ')
                employee_writer.writerow(days)

                for n in range(self._num_members):
                    row_shifts = []
                    row_shifts.append(self._names[n])
                    for d in range(self._num_days):
                        isWorking = False
                        if self.Value(self._shiftsA[(n, d)]):
                            row_shifts.append('A')
                            isWorking = True
                        if self.Value(self._shiftsP[(n, d)]):
                            row_shifts.append('P')
                            isWorking = True
                        if not isWorking:
                            row_shifts.append('X')
                    employee_writer.writerow(row_shifts)
                
        self._solution_count += 1

    def solution_count(self):
        return self._solution_count

def main():
    num_days = 31
    num_members = len(names)
    num_veterans = len(veterans)
    max_days = 5
    min_shiftsA_per_member = 7
    min_shiftsP_per_member = 7
    max_shiftsA_per_member = 12
    max_shiftsP_per_member = 12

    all_members = range(num_members)
    veteran_members = range(num_veterans)
    all_days = range(num_days)

    model = cp_model.CpModel()
    shiftsA = {}
    shiftsP = {}

    # make new variables
    for n in all_members:
        for d in all_days:
            shiftsA[(n, d)] = model.NewBoolVar('shiftA_n%id%i' % (n, d))
            shiftsP[(n, d)] = model.NewBoolVar('shiftP_n%id%i' % (n, d))

    # constraint: on 1 day at same shift, more than 2 members work
    for d in all_days:
        model.Add(sum(shiftsA[(n, d)] for n in all_members) >= 2)
        model.Add(sum(shiftsP[(n, d)] for n in all_members) >= 2)
        # at least one veteran for a shift a day
        model.Add(sum(shiftsA[n, d] for n in veteran_members) > 0)

    # constraint: 
    for n in all_members:
        for d in all_days:
            # members work only 1 time on each shift
            model.Add(shiftsA[(n, d)] <= 1)
            model.Add(shiftsP[(n, d)] <= 1)
            # members work only 1 shift a day
            model.Add((shiftsA[(n, d)] + shiftsP[(n, d)]) <= 1)
            # members can not work shift P and A consecutively
            if d < num_days - 1:
                model.Add((shiftsP[(n, d)] + shiftsA[(n, d+1)]) < 2)

            if d < num_days - max_days:
                sum_worked_days = 0
                for i in range(0, max_days):
                    sum_worked_days = sum_worked_days + shiftsA[(n, d + i)] + shiftsP[(n, d + i)]
                model.Add(sum_worked_days < max_days)

    for n in all_members:
        num_shiftsA_worked = sum(shiftsA[(n, d)] for d in all_days)
        num_shiftsP_worked = sum(shiftsP[(n, d)] for d in all_days)
        model.Add(min_shiftsA_per_member <= num_shiftsA_worked)
        model.Add(min_shiftsP_per_member <= num_shiftsP_worked)
        model.Add(num_shiftsA_worked <= max_shiftsA_per_member)
        model.Add(num_shiftsP_worked <= max_shiftsP_per_member)

    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 0
    a_few_solutions = range(5)
    solution_printer = MembersPartialSolutionPrinter(
        shiftsA, shiftsP, num_members, num_days, a_few_solutions, names
    )
    solver.SearchForAllSolutions(model, solution_printer)

    print()
    print('Statistics')
    print(' - conflicts             : %i' % solver.NumConflicts())
    print(' - branches              : %i' % solver.NumBranches())
    print(' - wall time             : %f s' % solver.WallTime())
    print(' - solutions found       : %i' % solution_printer.solution_count())

if __name__ == '__main__':
    main()