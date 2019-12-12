from __future__ import print_function
from ortools.sat.python import cp_model
import csv

names = ['박호원', '이보람', '정형섭', '남영선', '양혜경', '이찬희', '이장훈', '조인경']
veterans = ['박호원', '이보람', '정형섭', '남영선', '양혜경', '이찬희']

# schedule numbers
# 0 = X, 1 = A, 2 = P, 3 = 출장, 4 = 교육, 5 = 연차
categories = ['X', 'A', 'P', '출장', '교육', '연차']

class MembersPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, shifts, num_members, num_days, sols, names):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._shifts = shifts
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
                    # python has NO switch statements!
                    for d in range(self._num_days):
                        if self.Value(self._shifts[(n, d, 0)]):
                            row_shifts.append('X')
                        if self.Value(self._shifts[(n, d, 1)]):
                            row_shifts.append('A')
                        if self.Value(self._shifts[(n, d, 2)]):
                            row_shifts.append('P')
                        if self.Value(self._shifts[(n, d, 3)]):
                            row_shifts.append('출장')
                        if self.Value(self._shifts[(n, d, 4)]):
                            row_shifts.append('교육')
                        if self.Value(self._shifts[(n, d, 5)]):
                            row_shifts.append('연차')
                    employee_writer.writerow(row_shifts)
                
        self._solution_count += 1

    def solution_count(self):
        return self._solution_count

def main():
    num_days = 31
    num_members = len(names)
    num_veterans = len(veterans)
    max_days = 5
    min_shifts_per_member = 7
    max_shifts_per_member = 22
    num_categories = len(categories)

    all_members = range(num_members)
    veteran_members = range(num_veterans)
    all_days = range(num_days)
    all_categories = range(num_categories)

    model = cp_model.CpModel()

    # prepare shift dictionary
    requests = {}
    for n in all_members:
        for d in all_days:
            for s in all_categories:
                requests[(n, d, s)] = 0
    
    # request here / [(names, days, categories)]
    requests[(1, 15, 1)] = 1
    requests[(1, 16, 3)] = 1
    requests[(1, 17, 4)] = 1
    requests[(1, 18, 5)] = 1
    requests[(0, 0, 5)] = 1
    requests[(0, 1, 5)] = 1
    requests[(0, 2, 5)] = 1
    # for n in all_members:
    #     for d in all_days:
    #         for s in all_categories:
    #             print('requests[%i,%i,%i] : %i' % (n, d, s, requests[(n, d, s)]))

    # make new variables
    shifts = {}
    for n in all_members:
        for d in all_days:
            for s in all_categories:
                shifts[(n, d, s)] = model.NewBoolVar('shift_n%id%is%i' % (n, d, s))
    # for n in all_members:
    #     for d in all_days:
    #         for s in all_categories:
    #             print('shifts[%i,%i,%i] : %s' % (n, d, s, shifts[(n, d, s)]))

    # constraint: on 1 day at same shift, more than 2 members work
    for d in all_days:
        model.Add(sum(shifts[(n, d, 1)] for n in all_members) >= 2)
        model.Add(sum(shifts[(n, d, 2)] for n in all_members) >= 2)
        # at least one veteran for a shift a day
        model.Add(sum(shifts[(n, d, 1)] for n in veteran_members) > 0)
        model.Add(sum(shifts[(n, d, 2)] for n in veteran_members) > 0)

    # constraint: 
    for n in all_members:
        for d in all_days:
            # members work only 1 time on each shift
            model.Add(shifts[(n, d, 1)] <= 1)
            model.Add(shifts[(n, d, 2)] <= 1)
            # members work only 1 shift a day
            model.Add((shifts[(n, d, 1)] + shifts[(n, d, 2)]) <= 1)
            # members can not work shift P and A consecutively
            if d < num_days - 1:
                model.Add((shifts[(n, d, 2)] + shifts[(n, d + 1, 1)]) < 2)
            # members work at most 4 consecutive days
            if d < num_days - max_days:
                sum_worked_days = 0
                for i in range(0, max_days):
                    sum_worked_days = sum_worked_days + shifts[(n, d + i, 1)] + shifts[(n, d + i, 2)]
                model.Add(sum_worked_days < max_days)

    for n in all_members:
        num_shiftsX_worked = sum(shifts[(n, d, 0)] for d in all_days)
        num_shiftsA_worked = sum(shifts[(n, d, 1)] for d in all_days)
        num_shiftsP_worked = sum(shifts[(n, d, 2)] for d in all_days)
        model.Add(min_shifts_per_member <= num_shiftsX_worked)
        model.Add(min_shifts_per_member <= num_shiftsA_worked)
        model.Add(min_shifts_per_member <= num_shiftsP_worked)
        model.Add(num_shiftsX_worked <= max_shifts_per_member)
        model.Add(num_shiftsA_worked <= max_shifts_per_member)
        model.Add(num_shiftsP_worked <= max_shifts_per_member)
        # all days are required to be scheduled
        num_days_scheduled = sum(shifts[(n, d, s)] for d in all_days for s in all_categories)
        model.Add(num_days_scheduled == num_days)
        # 출장 = 3, should exactly match the number requested
        model.Add(sum(shifts[(n, d, 3)] for d in all_days) == sum(requests[(n, d, 3)] for d in all_days))
        # 교육 = 4, should exactly match the number requested
        model.Add(sum(shifts[(n, d, 4)] for d in all_days) == sum(requests[(n, d, 4)] for d in all_days))
        # 연차 = 5, should exactly match the number requested
        model.Add(sum(shifts[(n, d, 5)] for d in all_days) == sum(requests[(n, d, 5)] for d in all_days))

    for n in all_members:
        for d in all_days:
            for s in all_categories:
                if requests[(n, d, s)] > 0:
                    model.Add(shifts[(n, d, s)] == 1)

    # max_condition = 0
    # for n in all_members:
    #     for d in all_days:
    #         for s in all_categories:
    #             left = requests[(n, d, s)]
    #             # left = requests_dummy[n][d][s]
    #             right = shifts[(n, d, s)]
    #             max_condition = max_condition + left * right
    # # max_condition = sum(requests[(n, d, s)] * shifts[(n, d, s)] for n in all_members for d in all_days for s in all_categories)
    # model.Maximize(max_condition)

    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 0
    a_few_solutions = range(5)
    solution_printer = MembersPartialSolutionPrinter(
        shifts, num_members, num_days, a_few_solutions, names
    )
    solver.SearchForAllSolutions(model, solution_printer)

    print()
    print('Statistics')
    print(' - conflicts             : %i' % solver.NumConflicts())
    print(' - branches              : %i' % solver.NumBranches())
    print(' - wall time             : %f s' % solver.WallTime())
    print(' - solutions found       : %i' % solution_printer.solution_count())
    
    # solver.Solve(model)

    # with open('employee_file.csv', mode='w') as employee_file:
    #     employee_writer = csv.writer(
    #         employee_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL
    #     )
    #     days = list(range(1, num_days + 1))
    #     days.insert(0, ' ')
    #     employee_writer.writerow(days)

    #     for n in all_members:
    #         row_shifts = []
    #         row_shifts.append(names[n])
    #         # python has NO switch statements!
    #         for d in all_days:
    #             if solver.Value(shifts[(n, d, 0)]) == 1:
    #                 row_shifts.append('X')
    #             if solver.Value(shifts[(n, d, 1)]) == 1:
    #                 row_shifts.append('A')
    #             if solver.Value(shifts[(n, d, 2)]) == 1:
    #                 row_shifts.append('P')
    #             if solver.Value(shifts[(n, d, 3)]) == 1:
    #                 row_shifts.append('출장')
    #             if solver.Value(shifts[(n, d, 4)]) == 1:
    #                 row_shifts.append('교육')
    #             if solver.Value(shifts[(n, d, 5)]) == 1:
    #                 row_shifts.append('연차')
    #         employee_writer.writerow(row_shifts)

    # Statistics
    # print()
    # print('Statistics')
    # print('  - Number of shift requests met = %i' % solver.ObjectiveValue())
    # print('  - Wall time : %f s' % solver.WallTime())

if __name__ == '__main__':
    main()