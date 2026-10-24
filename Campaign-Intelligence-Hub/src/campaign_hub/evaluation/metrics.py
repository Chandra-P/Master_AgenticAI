import math


def citation_accuracy(cited, expected):
    cited=set(cited)
    return len(cited.intersection(expected))/len(cited) if cited else None


def retrieval_metrics(predicted, expected):
    predicted=list(dict.fromkeys(predicted))[:5]
    expected=set(expected)
    relevant=[int(x in expected) for x in predicted]
    dcg=sum(v/math.log2(i+2) for i,v in enumerate(relevant))
    ideal=sum(1/math.log2(i+2) for i in range(min(5,len(expected))))
    return {'mrr': next((1/(i+1) for i,v in enumerate(relevant) if v),0),
            'ndcg':dcg/ideal if ideal else None,
            'context_precision':sum(relevant)/len(predicted) if predicted else 0,
            'context_recall':sum(relevant)/len(expected) if expected else None}
