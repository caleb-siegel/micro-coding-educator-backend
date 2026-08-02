from typing import List, Optional, Literal, Union
from pydantic import BaseModel, Field

# Card Types
CardType = Literal[
    'hook',
    'multiple_choice',
    'drag_to_order',
    'match_pairs',
    'spot_the_mistake',
    'choose_the_tradeoff',
    'build_the_system',
    'predict_what_happens',
    'before_vs_after',
    'guess_the_metric',
    'timeline',
    'takeaway'
]

class BaseCardModel(BaseModel):
    id: str
    type: CardType
    title: Optional[str] = None
    subtitle: Optional[str] = None
    hint: Optional[str] = None
    simpleExplanation: Optional[str] = None

class HookCardModel(BaseCardModel):
    type: Literal['hook'] = 'hook'
    headline: str
    body: str
    statBadge: Optional[dict] = None
    iconName: Optional[str] = 'Sparkles'

class OptionModel(BaseModel):
    id: str
    text: str
    isCorrect: bool
    explanation: str

class MultipleChoiceCardModel(BaseCardModel):
    type: Literal['multiple_choice'] = 'multiple_choice'
    question: str
    options: List[OptionModel]

class DragItemModel(BaseModel):
    id: str
    label: str
    correctIndex: int

class DragToOrderCardModel(BaseCardModel):
    type: Literal['drag_to_order'] = 'drag_to_order'
    instruction: str
    items: List[DragItemModel]
    explanation: str

class MatchPairItemModel(BaseModel):
    id: str
    left: str
    right: str

class MatchPairsCardModel(BaseCardModel):
    type: Literal['match_pairs'] = 'match_pairs'
    instruction: str
    pairs: List[MatchPairItemModel]
    explanation: str

class DiagramNodeModel(BaseModel):
    id: str
    label: str
    isMistake: bool
    subtext: Optional[str] = None

class CodeLineModel(BaseModel):
    line: int
    text: str
    isMistake: bool

class ContextCodeOrDiagramModel(BaseModel):
    type: Literal['code', 'diagram']
    content: str
    nodes: Optional[List[DiagramNodeModel]] = None
    codeLines: Optional[List[CodeLineModel]] = None

class SpotTheMistakeCardModel(BaseCardModel):
    type: Literal['spot_the_mistake'] = 'spot_the_mistake'
    instruction: str
    question: Optional[str] = None
    contextCodeOrDiagram: ContextCodeOrDiagramModel
    explanation: str

class TradeoffOptionModel(BaseModel):
    id: str
    title: str
    pros: List[str]
    cons: List[str]
    isBestChoice: bool
    why: str

class ChooseTheTradeoffCardModel(BaseCardModel):
    type: Literal['choose_the_tradeoff'] = 'choose_the_tradeoff'
    scenario: str
    options: List[TradeoffOptionModel]

class ArchitectureBlockModel(BaseModel):
    id: str
    label: str
    icon: str

class TargetSlotModel(BaseModel):
    slotId: str
    label: str
    correctBlockId: str

class BuildTheSystemCardModel(BaseCardModel):
    type: Literal['build_the_system'] = 'build_the_system'
    task: str
    availableBlocks: List[ArchitectureBlockModel]
    targetSlots: List[TargetSlotModel]
    explanation: str

class OutcomeModel(BaseModel):
    threshold: int
    title: str
    status: Literal['success', 'warning', 'critical']
    description: str
    diagramState: str

class PredictWhatHappensCardModel(BaseCardModel):
    type: Literal['predict_what_happens'] = 'predict_what_happens'
    scenario: str
    metricLabel: str
    minVal: int
    maxVal: int
    unit: str
    outcomes: List[OutcomeModel]
    targetValue: int
    explanation: str

class MetricItemModel(BaseModel):
    label: str
    value: str

class TopologyOptionModel(BaseModel):
    id: str
    label: str
    diagramType: str
    metrics: List[MetricItemModel]
    isBetter: bool

class BeforeVsAfterCardModel(BaseCardModel):
    type: Literal['before_vs_after'] = 'before_vs_after'
    question: str
    optionA: TopologyOptionModel
    optionB: TopologyOptionModel
    explanation: str

class ChartPointModel(BaseModel):
    time: str
    value: int
    spike: Optional[bool] = False

class MetricChoiceModel(BaseModel):
    id: str
    label: str
    isCorrect: bool
    explanation: str

class GuessTheMetricCardModel(BaseCardModel):
    type: Literal['guess_the_metric'] = 'guess_the_metric'
    metricTitle: str
    chartData: List[ChartPointModel]
    question: str
    choices: List[MetricChoiceModel]

class EventModel(BaseModel):
    id: str
    title: str
    description: str
    correctOrder: int

class TimelineCardModel(BaseCardModel):
    type: Literal['timeline'] = 'timeline'
    title: str
    instruction: str
    events: List[EventModel]
    explanation: str

class TakeawayCardModel(BaseCardModel):
    type: Literal['takeaway'] = 'takeaway'
    oneSentenceSummary: str
    keyInsights: List[str]
    suggestedNextTopic: Optional[str] = 'System Design'

LessonCardUnion = Union[
    HookCardModel,
    MultipleChoiceCardModel,
    DragToOrderCardModel,
    MatchPairsCardModel,
    SpotTheMistakeCardModel,
    ChooseTheTradeoffCardModel,
    BuildTheSystemCardModel,
    PredictWhatHappensCardModel,
    BeforeVsAfterCardModel,
    GuessTheMetricCardModel,
    TimelineCardModel,
    TakeawayCardModel
]

class LessonResponseModel(BaseModel):
    id: str
    title: str
    topic: str
    difficulty: str
    durationMinutes: int
    subtitle: str
    cards: List[dict]

class GenerateLessonRequest(BaseModel):
    topic: str
    difficulty: Optional[str] = 'Foundational'
    durationMinutes: Optional[int] = 5
