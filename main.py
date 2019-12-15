from __future__ import print_function
from ortools.sat.python import cp_model
import csv
import datetime
import calendar
import xlsxwriter

first_day = datetime.datetime(2020, 1, 1)
day_offs = [4, 5, 11, 12, 18, 19, 23, 24, 25, 26]

# names of working members (VETERANS SHOULD BE AT THE LEFT OF ROW)
names = ['박호원', '이보람', '정형섭', '남영선', '양혜경', '이찬희', '이장훈', '조인경']
veterans = ['박호원', '이보람', '정형섭', '남영선', '양혜경', '이찬희']

# schedule numbers
# 0 = X, 1 = A, 2 = P, 3 = 출장, 4 = 교육, 5 = 연차, 6 = D
categories = ['X', 'A', 'P', '출장', '교육', '연차', 'D']

def dayName(weekday):
    if weekday == 0:
        return "월"
    if weekday == 1:
        return "화"
    if weekday == 2:
        return "수"
    if weekday == 3:
        return "목"
    if weekday == 4:
        return "금"
    if weekday == 5:
        return "토"
    if weekday == 6:
        return "일"


class MembersPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, shifts, num_members, num_days, sols, names, first_day):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._shifts = shifts
        self._num_members = num_members
        self._num_days = num_days
        self._solutions = set(sols)
        self._solution_count = 0
        self._names = names
        self._first_day = first_day

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            print('Solution %i' % self._solution_count)
            # Create an new Excel file and convert the text data.
            workbook = xlsxwriter.Workbook('solution_{}.xlsx'.format(self._solution_count))
            worksheet = workbook.add_worksheet()
            worksheet.set_column('B:AZ', 4)
            # Start from the first cell.
            row = 0
            col = 0

            lines = []

            days = []
            weekdays = []
            the_day = datetime.datetime(self._first_day.year, self._first_day.month, self._first_day.day)
            i = 0
            while i < self._num_days:
                days.append(the_day.day)
                weekdays.append(dayName(the_day.weekday()))
                the_day += datetime.timedelta(days = 1)
                i += 1

            days.insert(0, ' ')
            lines.append(days)

            weekdays.insert(0, ' ')
            categories_row = categories.copy()
            categories_row.insert(0, ' ')
            titles = weekdays + categories_row
            lines.append(titles)
            
            shiftsA = { day: 0 for day in range(self._num_days) }
            shiftsP = { day: 0 for day in range(self._num_days) }

            for n in range(self._num_members):
                row_shifts = []
                summary = { category: 0 for category in range(len(categories)) } 
                row_shifts.append(self._names[n])
                # python has NO switch statements!
                for d in range(self._num_days):
                    if self.Value(self._shifts[(n, d, 0)]):
                        row_shifts.append('X')
                        summary[0] += 1
                        # print('%s day %i X' % (names[n], d))
                    if self.Value(self._shifts[(n, d, 1)]):
                        row_shifts.append('A')
                        shiftsA[d] += 1
                        summary[1] += 1
                        # print('%s day %i A' % (names[n], d))
                    if self.Value(self._shifts[(n, d, 2)]):
                        row_shifts.append('P')
                        shiftsP[d] += 1
                        summary[2] += 1
                        # print('%s day %i P' % (names[n], d))
                    if self.Value(self._shifts[(n, d, 3)]):
                        row_shifts.append('출장')
                        summary[3] += 1
                        # print('%s day %i 출장' % (names[n], d))
                    if self.Value(self._shifts[(n, d, 4)]):
                        row_shifts.append('교육')
                        summary[4] += 1
                        # print('%s day %i 교육' % (names[n], d))
                    if self.Value(self._shifts[(n, d, 5)]):
                        row_shifts.append('연차')
                        summary[5] += 1
                        # print('%s day %i 연차' % (names[n], d))
                    if self.Value(self._shifts[(n, d, 6)]):
                        row_shifts.append('D')
                        summary[6] += 1
                row_shifts.append('')
                print(summary)
                row_shifts += summary.values()
                lines.append(row_shifts)
            
            lines.append([''])

            rowA = []
            rowA.append('A')
            rowA += shiftsA.values()
            lines.append(rowA)
            
            rowP = []
            rowP.append('P')
            rowP += shiftsP.values()
            lines.append(rowP)
            # print(lines)
            for line in lines:
                print(line)
                col = 0
                for item in line:
                    cell_format = workbook.add_format()
                    cell_format.set_border()
                    cell_format.set_align('center')
                    if col in day_offs:
                        cell_format.set_bg_color('orange')
                    # Write any other lines to the worksheet.
                    worksheet.write(row, col, item, cell_format)
                    col += 1

                row += 1
            workbook.close()

        self._solution_count += 1

    def solution_count(self):
        return self._solution_count



def main():
    num_days = calendar.monthrange(first_day.year, first_day.day)[1]
    num_members = len(names)
    num_veterans = len(veterans)
    num_X = 11
    min_shifts_per_member = num_days - num_X
    num_categories = len(categories)

    all_members = range(num_members)
    veteran_members = range(num_veterans)
    all_days = range(num_days)
    all_categories = range(num_categories)
    worked_categories = range(1, num_categories)

    model = cp_model.CpModel()

    # prepare shift dictionary
    requests = {}
    for n in all_members:
        for d in all_days:
            for s in all_categories:
                requests[(n, d, s)] = 0
    
    # specific request here / [(names, days, categories)]
    requests[(0, 22, 0)] = 1
    requests[(0, 23, 0)] = 1
    requests[(0, 24, 0)] = 1
    requests[(0, 25, 0)] = 1
    requests[(0, 26, 0)] = 1
    requests[(1, 0, 0)] = 1
    requests[(1, 5, 4)] = 1
    requests[(1, 6, 4)] = 1
    requests[(1, 7, 4)] = 1
    requests[(1, 8, 4)] = 1
    requests[(1, 9, 4)] = 1
    requests[(1, 23, 1)] = 1
    requests[(1, 24, 1)] = 1
    requests[(1, 25, 0)] = 1
    requests[(1, 26, 0)] = 1
    requests[(1, 27, 0)] = 1
    requests[(1, 28, 0)] = 1
    requests[(1, 29, 1)] = 1
    requests[(1, 30, 1)] = 1
    requests[(3, 0, 0)] = 1
    requests[(3, 5, 4)] = 1
    requests[(3, 6, 4)] = 1
    requests[(3, 7, 4)] = 1
    requests[(3, 8, 4)] = 1
    requests[(3, 9, 4)] = 1
    requests[(4, 0, 2)] = 1
    requests[(4, 20, 5)] = 1
    requests[(4, 25, 2)] = 1
    requests[(4, 26, 2)] = 1
    requests[(5, 10, 5)] = 1
    requests[(5, 11, 5)] = 1
    requests[(5, 12, 5)] = 1
    requests[(5, 13, 0)] = 1
    requests[(5, 14, 0)] = 1
    requests[(5, 15, 0)] = 1
    requests[(5, 16, 0)] = 1
    requests[(6, 9, 6)] = 1
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
            # members work only 1 category of shift a day
            model.Add(sum(shifts[(n, d, s)] for s in all_categories) <= 1)
            # members can not work shift P and A consecutively
            if d < num_days - 1:
                model.Add((shifts[(n, d, 2)] + shifts[(n, d + 1, 1)]) < 2)
            # members work at most 5 consecutive days
            if d < num_days - 6:
                sum_worked_days = 0
                for i in range(0, 6):
                    sum_worked_days = sum_worked_days + shifts[(n, d + i, 1)] + shifts[(n, d + i, 2)] + shifts[(n, d + i, 3)] + shifts[(n, d + i, 4)] + shifts[(n, d + i, 6)]
                model.Add(sum_worked_days < 6)
            # in 2 weeks, members work at most 10 days
            if d < num_days - 14:
                sum_worked_days = 0
                for i in range(0, 14):
                    sum_worked_days = sum_worked_days + shifts[(n, d + i, 1)] + shifts[(n, d + i, 2)] + shifts[(n, d + i, 3)] + shifts[(n, d + i, 4)] + shifts[(n, d + i, 6)]
                model.Add(sum_worked_days <= 10)

    for n in all_members:
        # minimum working days: all categories except X take up at least 20 days
        # model.Add(num_X == sum(shifts[(n, d, 0)] for d in all_days))
        model.Add(min_shifts_per_member == sum(shifts[(n, d, s)] for d in all_days for s in worked_categories))
        # maximum working days: all working categories take up at most 22 days
        # model.Add(sum(shifts[(n, d, s)] for d in all_days for s in worked_categories) <= max_shifts_per_member)
        # model.Add(sum(shifts[(n, d, 0)] for d in all_days) <= max_shifts_per_member)
        # model.Add(sum(shifts[(n, d, 1)] for d in all_days) <= max_shifts_per_member)
        # model.Add(sum(shifts[(n, d, 2)] for d in all_days) <= max_shifts_per_member)
        # all days are required to be scheduled
        model.Add(sum(shifts[(n, d, s)] for d in all_days for s in all_categories) == num_days)
        # 출장 = 3, should exactly match the number requested
        model.Add(sum(shifts[(n, d, 3)] for d in all_days) == sum(requests[(n, d, 3)] for d in all_days))
        # 교육 = 4, should exactly match the number requested
        model.Add(sum(shifts[(n, d, 4)] for d in all_days) == sum(requests[(n, d, 4)] for d in all_days))
        # 연차 = 5, should exactly match the number requested
        model.Add(sum(shifts[(n, d, 5)] for d in all_days) == sum(requests[(n, d, 5)] for d in all_days))
        # D = 6, should exactly match the number requested
        model.Add(sum(shifts[(n, d, 6)] for d in all_days) == sum(requests[(n, d, 6)] for d in all_days))

    # special requests '박호원', '이보람', '정형섭', '남영선', '양혜경', '이찬희', '이장훈', '조인경'
    # like balance between A and P 
 
    # 박호원
    model.Add(sum(shifts[(0, d, 1)] for d in all_days) > 6)
    model.Add(sum(shifts[(0, d, 2)] for d in all_days) > 6)

    # 이보람
    model.Add(sum(shifts[(1, d, 1)] for d in all_days) > 6)
    model.Add(sum(shifts[(1, d, 2)] for d in all_days) > 6)
    model.Add(shifts[(1, 3, 2)] == 0)
    model.Add(shifts[(1, 4, 2)] == 0)
    model.Add(shifts[(1, 10, 2)] == 0)
    model.Add(shifts[(1, 11, 2)] == 0)
    model.Add(shifts[(1, 17, 2)] == 0)
    model.Add(shifts[(1, 18, 2)] == 0)

    # 정형섭
    model.Add(sum(shifts[(2, d, 1)] for d in all_days) > 6)
    model.Add(sum(shifts[(2, d, 2)] for d in all_days) > 6)

    # 남영선
    model.Add(sum(shifts[(3, d, 1)] for d in all_days) > 6)
    model.Add(sum(shifts[(3, d, 2)] for d in all_days) > 6)

    # 양혜경 wants all P shifts, in other words no A shifts
    model.Add(sum(shifts[(4, d, 1)] for d in all_days) == 0)
    # model.Add(sum(shifts[(4, d, 1)] for d in all_days) > 7)
    # model.Add(sum(shifts[(4, d, 2)] for d in all_days) > 7)
    
    # 이찬희
    model.Add(sum(shifts[(5, d, 1)] for d in all_days) > 6)
    model.Add(sum(shifts[(5, d, 2)] for d in all_days) > 6)

    # 이장훈
    model.Add(sum(shifts[(6, d, 1)] for d in all_days) > 6)
    model.Add(sum(shifts[(6, d, 2)] for d in all_days) > 6)

    # 조인경
    model.Add(sum(shifts[(6, d, 1)] for d in all_days) > 6)
    model.Add(sum(shifts[(6, d, 2)] for d in all_days) > 6)

    # last day last month P => NO A on the first day 
    model.Add(shifts[(0, 0, 1)] == 0)
    model.Add(shifts[(1, 0, 1)] == 0)
    model.Add(shifts[(3, 0, 1)] == 0)

    # max_condition = sum(requests[(n, d, s)] * shifts[(n, d, s)] for n in all_members for d in all_days for s in all_categories)
    # model.Maximize(max_condition)
    for n in all_members:
        for d in all_days:
            for s in all_categories:
                if requests[(n, d, s)]:
                    model.Add(shifts[(n, d, s)] == 1)

    solver = cp_model.CpSolver()
    # solver.parameters.linearization_level = 1
    solver.parameters.max_time_in_seconds = 10.0
    a_few_solutions = range(10)
    solution_printer = MembersPartialSolutionPrinter(
        shifts, num_members, num_days, a_few_solutions, names, first_day
    )
    solver.SearchForAllSolutions(model, solution_printer)
    # solver.SolveWithSolutionCallback(model, solution_printer)

    print()
    print('Statistics')
    print(' - conflicts             : %i' % solver.NumConflicts())
    print(' - shift requests met    : %i' % solver.ObjectiveValue())
    print(' - branches              : %i' % solver.NumBranches())
    print(' - wall time             : %f s' % solver.WallTime())
    print(' - solutions found       : %i' % solution_printer.solution_count())
    
if __name__ == '__main__':
    main()