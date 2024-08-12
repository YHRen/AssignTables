import random
import itertools as it
import argparse
import pandas as pd
import numpy as np
from tqdm import tqdm
from tqdm.auto import trange
import matplotlib.pyplot as plt


def get_tech_topics(df):
    all_tech_topics = set()
    for topic in df["Technical Interests"]:
        topic = topic.rstrip(";")
        if ";" in topic:
            ta, tb = topic.split(";")
            all_tech_topics.add(ta)
            all_tech_topics.add(tb)
        else:
            all_tech_topics.add(topic)

    # print(all_tech_topics)
    tech2idx = {x: y for x, y in zip(all_tech_topics, range(len(all_tech_topics)))}
    return tech2idx


def attach_tech_code(df, tech2idx, name="Tech One Hot"):
    tech_code = []
    for topic in df["Technical Interests"]:
        topic = topic.rstrip(";")
        tmp = np.zeros(len(tech2idx), dtype=int)
        if ";" in topic:
            ta, tb = topic.split(";")
            tmp[tech2idx[ta]] = 1
            tmp[tech2idx[tb]] = 1
        else:
            tmp[tech2idx[topic]] = 1
        tech_code.append(tmp)
    df[name] = tech_code


def attach_feat_index(df, ft_names):
    ft_idx_names = []
    for ft in ft_names:
        tmp = df[ft].unique().tolist()
        name2idx = {x: y for x, y in zip(tmp, range(len(tmp)))}
        df[ft + " Index"] = df[ft].apply(lambda x: name2idx[x])
        ft_idx_names.append(ft + " Index")
    return ft_idx_names


def init_assignment(N, M):
    mtx = [[] for _ in range(M)]
    for i in range(N):
        mtx[i % M].append(i)
    return mtx


def show_assignment(mtx):
    for row in mtx:
        print(row)


def show_table(row, feat):
    for x in row:
        print(x, ":", feat[x])


def cal_diversity_score(row, feats, paras):
    """
    N := # of participants
    F := # of features
    row: a table of person id
    feats: N x F
    paras: F
    return: a score higher the better
    """
    fsz = feats.shape[1]
    # print(row)
    # print(feats.shape)
    sub = feats[row]
    rst = []
    for k, b in zip(range(fsz), paras):
        tmp = np.unique(sub[:, k])
        tmp = len(tmp)
        scr = np.power(b, tmp)  # diversity is preferred exponentially
        rst.append(scr)
    return rst


def is_move(prv, nxt, T):
    if nxt > prv:
        return 1
    else:
        prob = np.exp((nxt - prv) / T)
        # print(prob)
        return random.random() < prob


def cal_tech_alignmnt(row, tech, para):
    """
    N := # of participants
    T := # of tech topics
    row: a table of person id
    tech: N x T
    para: 1
    return: a score higher the better
    """
    rst = (
        tech[row].sum(axis=0).max()
    )  # maximum topic overlap in the table, higher the better
    rst = np.power(para, rst)
    return rst


def cal_s(row, feats, feat_paras, tech, tech_para, linweights):
    scr = cal_diversity_score(row, feats, feat_paras)
    scr.append(cal_tech_alignmnt(row, tech, tech_para))
    # print(scr)

    # dot prod
    rst = 0.0
    for x, y in zip(scr, linweights):
        rst += x * y

    return rst


def cal_all_score(mtx, feats, feat_paras, tech, tech_para, linweights):
    rst = 0.0
    for row in mtx:
        rst += cal_s(row, feats, feat_paras, tech, tech_para, linweights)
    return rst


def report_table(df, row, tech, idx2tech):
    top_topic = tech[row].sum(axis=0).argmax()
    print(f"Top Topic: {idx2tech[top_topic]}")
    print(np.stack(tech[row]))
    ft = ["Name", "Primary Organization", "Years at BNL", "Career State"]
    print(df.iloc[row][ft])


def report_all(df, mtx, tech, idx2tech):
    for idx, row in zip(range(len(mtx)), mtx):
        print("\n" + "-" * 30 + f"{idx+1:02d}" + "-" * 30 + "\n")
        report_table(df, row, tech, idx2tech)


def top_topic(row, tech, idx2tech):
    toptopic = tech[row].sum(axis=0).argmax()
    return idx2tech[toptopic]


def export_all(df, mtx, tech, idx2tech, outfile):
    df[["Table ID", "Topic"]] = [int(0), "None"]
    for row, table_id in zip(mtx, it.count(1)):
        topic = idx2tech[tech[row].sum(axis=0).argmax()]
        df.loc[row, ["Table ID", "Topic"]] = [table_id, topic]
    df.to_excel(outfile, columns=["Name", "Primary Organization", "Table ID", "Topic"])


def main():
    # fn = "ACoP Networking Kickoff Registration(1-46).xlsx"

    parser = argparse.ArgumentParser(description="Assign participants to tables.")
    parser.add_argument("input", type=str)
    parser.add_argument(
        "-m", "--number-of-tables", type=int, required=True
    )
    args = parser.parse_args()

    df = pd.read_excel(args.input)
    # print(df.columns)
    assert len(df["Name"].unique()) == len(df)

    # Define constants and Set parameters
    N = len(df)  # number of participants
    M = args.number_of_tables  # number of tables
    print(f"N = {N}, M = {M}")

    #  score is calculated as $base^diverse$.
    feat_para = [1.4, 1.2, 1.2]
    tech_para = 1.4

    # linear weights for ft_names + ["tech topic"]
    linweights = [1, 1, 1, 0.5]

    # Temperature, in -A*ln(t)+A
    steps = 1 << 8
    microsteps = 1 << 10
    A = 0.5

    # Process DF and Extract Feat and Tech from DataFrame
    tech2idx = get_tech_topics(df)
    idx2tech = {x: y for y, x in tech2idx.items()}
    attach_tech_code(df, tech2idx, name="Tech One Hot")
    ft_idx_names = attach_feat_index(
        df, ft_names=["Primary Organization", "Years at BNL", "Career State"]
    )
    feat = df[ft_idx_names].to_numpy(dtype=int)
    tech = np.stack(df["Tech One Hot"].tolist())

    mtx = init_assignment(N, M)
    # show_assignment(mtx)

    tbl_idx = list(range(M))
    # A = 0.5
    # steps = 100
    ts = np.linspace(1 / steps, 1 - 1 / steps, int(steps - 1))
    # plt.plot(x,-1*np.log(x))

    score_log = []
    tts = tqdm(total=len(ts), position=0, leave=True, ncols=80, ascii=True)
    for t in ts:
        tts.update()
        temp = -A * np.log(t)
        accpt = 0
        for _ in range(microsteps):
            # pick random two tables
            random.shuffle(tbl_idx)
            idx_a, idx_b = tbl_idx[:2]

            prv_scr = cal_s(mtx[idx_a], feat, feat_para, tech, tech_para, linweights)
            prv_scr += cal_s(mtx[idx_b], feat, feat_para, tech, tech_para, linweights)

            # pick two persons and swap
            random.shuffle(mtx[idx_a])
            random.shuffle(mtx[idx_b])
            mtx[idx_a][0], mtx[idx_b][0] = mtx[idx_b][0], mtx[idx_a][0]

            nxt_scr = cal_s(mtx[idx_a], feat, feat_para, tech, tech_para, linweights)
            nxt_scr += cal_s(mtx[idx_b], feat, feat_para, tech, tech_para, linweights)

            # if walk
            if is_move(prv_scr, nxt_scr, temp):
                accpt += 1
                pass
            else:
                # unswap
                mtx[idx_a][0], mtx[idx_b][0] = mtx[idx_b][0], mtx[idx_a][0]
        tmp = cal_all_score(mtx, feat, feat_para, tech, tech_para, linweights)
        score_log.append(tmp)
        tts.set_postfix(score=tmp)
        # print(f"{t:.4f}: score {tmp:.4f}, accpt {accpt/microsteps:.4f}")

    report_all(df, mtx, tech, idx2tech)
    export_all(df, mtx, tech, idx2tech, f"table_assignment_{M}.xlsx")
    plt.plot(score_log)
    plt.savefig(f"table_assignment_{M}_score_log.png", dpi=300)


if __name__ == "__main__":
    main()
