import sys

par_debugging = False


def debug(*args, end="\n"):
    global par_debugging
    if par_debugging:
        print(*args, end=end, file=sys.stderr, flush=True)


# ====================================
class FluidBox:
    def __init__(self):
        self.name = ""
        self.short_name = ""
        self.base_area = 0
        self.base_level = 0
        self.height = 0
        self.amount = 0.0
        self.speed = 0.0

    def max_fluid_capacity(self):
        return self.base_area * self.height * 100


# ====================================
class pipe(FluidBox):
    def __init__(self):
        self.name = "pipe"
        self.short_name = "pipe"
        self.base_area = 1
        self.base_level = 0
        self.height = 1
        self.amount = 0.0
        self.speed = 0.0


class inf_pipe(FluidBox):
    def __init__(self):
        self.name = "inf_pipe"
        self.short_name = "inf"
        self.base_area = 1
        self.base_level = 0
        self.height = 1
        self.amount = 0.0
        self.speed = 0.0


class offshore_pump(FluidBox):
    def __init__(self):
        self.name = "offshore_pump"
        self.short_name = "Opump"
        self.base_area = 1
        self.base_level = 1
        self.height = 1
        self.amount = 0.0
        self.speed = 0.0


class storage_tank(FluidBox):
    def __init__(self, a=0):
        self.name = "storage_tank"
        self.short_name = "tank"
        self.base_area = 250
        self.base_level = 0
        self.height = 1
        self.amount = a
        self.speed = 0.0


class pump(FluidBox):
    def __init__(self):
        self.name = "pump"
        self.short_name = "pump"
        self.base_area = 1
        self.base_level = 0
        self.height = 4
        self.amount = 0.0
        self.speed = 0.0
        self.pumping_speed = 200


# ====================================
class Segment:
    def __init__(self, p, o=None):
        self.pipes = p
        if o is None:
            self.order_of_construction = tuple(range(1, len(p)))
        else:
            self.order_of_construction = o

        debug(
            "self.order_of_construction = ",
            type(self.order_of_construction),
            self.order_of_construction,
        )


# ====================================
def print_pipes(all_pipes):
    separator = " || "
    line1 = line2 = line3 = ""
    line4 = line5 = line6 = ""
    for segment in all_pipes:
        p = segment.pipes
        line1 += " ".join("{:>8s}".format(k.short_name) for k in p) + separator
        line2 += (
            " ".join("{:>8.1f}".format(k.max_fluid_capacity()) for k in p) + separator
        )
        line3 += " ".join("{:>8.1f}".format(k.base_level) for k in p) + separator
        line4 += " ".join("{:>8.1f}".format(k.amount) for k in p) + separator
        line5 += " ".join("{:>8.1f}".format(k.speed) for k in p) + separator
        line6 += " ".join("{:>8.1f}".format(k.speed * 60.0) for k in p) + separator
    print("       \t", line1)
    print("volume:\t", line2)
    print("baseL:\t", line3)
    print("amount:\t", line4)
    print("speed:\t", line5)
    print("speed:\t", line6)
    print()


# ====================================
def fluid_update(segment):
    global par_debugging
    pipes = segment.pipes
    for p in pipes:
        if p.name == "offshore_pump":
            p.amount = 20.0
        if p.name == "inf_pipe":
            p.amount = 0.0

    for i in segment.order_of_construction:
        if i > 0 and i < len(pipes):
            # print(" i = {}".format(i))
            if pipes[i].name == "pump":
                # s - how much liquid to move
                s = pipes[i].pumping_speed  # 200 - vanilla
                if s > pipes[i - 1].amount:
                    s = pipes[i - 1].amount

                if pipes[i].amount + s > pipes[i].max_fluid_capacity():
                    s = pipes[i].max_fluid_capacity() - pipes[i].amount

                debug("s={0}".format(s))

                pipes[i - 1].amount -= s
                pipes[i].amount += s
                pipes[i].speed = s
            else:
                # from IDA Free
                # v15 = (v4->invertedBaseArea * amount + v4->baseLevel - (target->invertedBaseArea * v11 + target->baseLevel))
                #     * 0.4000000059604645
                #     + (float)(fminf(v4->volume * 0.1, v2->speed * 0.58999997) - fminf(volume * 0.1, *(float *)(v6 + 12) * 0.58999997));

                # https://forums.factorio.com/viewtopic.php?f=18&t=19851
                # Pressure_A
                xmm6 = (
                    pipes[i - 1].amount / pipes[i - 1].base_area
                    + pipes[i - 1].base_level * 100
                )
                # Pressure_B
                xmm1 = pipes[i].amount / pipes[i].base_area + pipes[i].base_level * 100
                debug("{0} ========================".format(i))
                debug("xmm6={0}, xmm1={1}".format(xmm6, xmm1))

                # Limited[Previous_Flow * 0.59, Target_Capacity * 0.1]
                if pipes[i].speed >= 0.0:
                    xmm4 = pipes[i - 1].max_fluid_capacity() * 0.1
                    xmm0 = pipes[i].speed * 0.58999997
                    debug("xmm4={0}, xmm0={1}".format(xmm4, xmm0))

                    xmm4 = min(xmm4, xmm0)
                    debug("xmm4={0}".format(xmm4))
                else:
                    xmm4 = pipes[i].max_fluid_capacity() * -0.1
                    xmm0 = pipes[i].speed * 0.58999997
                    debug("xmm4={0}, xmm0={1}".format(xmm4, xmm0))

                    xmm4 = max(xmm4, xmm0)
                    debug("xmm4={0}".format(xmm4))

                xmm6 -= xmm1  # (Pressure_A - Pressure_B)
                debug("xmm6={0}".format(xmm6))

                xmm6 *= 0.4  # (Pressure_A - Pressure_B) * 0.4
                debug("xmm6={0}".format(xmm6))

                xmm6 += xmm4  # (Pressure_A - Pressure_B) * 0.4 + Limited[Previous_Flow * 0.59, Target_Capacity * 0.1]
                debug("xmm6={0}".format(xmm6))

                # s - how much liquid to move
                s = xmm6
                if s >= 0.0:
                    if s > pipes[i - 1].amount:
                        s = pipes[i - 1].amount

                    if pipes[i].amount + s > pipes[i].max_fluid_capacity():
                        s = pipes[i].max_fluid_capacity() - pipes[i].amount

                    debug("s={0}".format(s))

                    pipes[i - 1].amount -= s
                    pipes[i].amount += s
                    pipes[i].speed = s
                else:
                    s *= -1.0
                    if s > pipes[i].amount:
                        s = pipes[i].amount

                    if pipes[i - 1].amount + s > pipes[i - 1].max_fluid_capacity():
                        s = pipes[i - 1].max_fluid_capacity() - pipes[i - 1].amount

                    debug("s={0}".format(s))

                    pipes[i - 1].amount += s
                    pipes[i].amount -= s
                    pipes[i].speed = -1.0 * s

            if par_debugging:
                print_pipes(pipes)


# ====================================
pipes1 = []
pipes1.append(offshore_pump())
pipes1.append(pipe())
pipes1.append(pipe())
pipes1.append(pipe())
pipes1.append(pipe())
pipes1.append(inf_pipe())

pipes2 = []
pipes2.append(offshore_pump())
pipes2.append(pipe())
pipes2.append(pipe())
pipes2.append(pipe())
pipes2.append(pipe())
pipes2.append(inf_pipe())

pipes3 = []
pipes3.append(offshore_pump())
pipes3.append(pipe())
pipes3.append(storage_tank())

pipes4 = []
pipes4.append(storage_tank(25000))
pipes4.append(pump())
pipes4.append(storage_tank())

all_pipes = []
all_pipes.append(Segment(pipes1))
all_pipes.append(Segment(pipes2, (5, 4, 3, 2, 1)))
all_pipes.append(Segment(pipes3))
all_pipes.append(Segment(pipes4))


print("tick = {0}".format(0))
print_pipes(all_pipes)

max_tick = 100
print_every_N_ticks = 10
for tick in range(max_tick):
    for p in all_pipes:
        fluid_update(p)

    if (tick + 1) % print_every_N_ticks == 0 or tick == 0 or tick == max_tick:
        print("tick = {0}".format(tick + 1))
        print_pipes(all_pipes)
