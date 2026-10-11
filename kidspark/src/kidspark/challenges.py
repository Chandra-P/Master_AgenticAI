"""Reviewed learning stories with short questions and separate fact panels."""
from dataclasses import dataclass
from random import Random

CHALLENGES = ('Smart Shopping', 'Spot the Scam', 'Plan an Event')
LEVELS = ('Middle school', 'High school')
# ROUNDS preserves version 1; new practice uses the expanded version-2 bank.
CONTENT_VERSION = '2'
STORIES = {'Smart Shopping': ('🛍️', 'Outing supply squad', 'Help your friends pack for a school outing. Find good deals without stretching the budget.'), 'Spot the Scam': ('🔎', 'Message detective', 'Help your fictional friend Sam check five messages. Pause, look for clues, and choose a safe next step.'), 'Plan an Event': ('🎉', 'Celebration crew', 'Help your class plan a celebration. Make room for fun while keeping costs under control.')}
TAKEAWAYS = {'Smart Shopping': 'Compare the cost for one item, then check the whole purchase against your budget.', 'Spot the Scam': 'Pause before acting. Check messages through a channel you already trust, and ask a trusted adult when unsure.', 'Plan an Event': 'Add all the costs and leave a little room for surprises.'}

@dataclass(frozen=True)
class Question:
    id: str
    prompt: str
    choices: tuple[str, ...]
    correct_index: int
    skill: str
    hint: str
    explanation: str
    scenario: str

    @property
    def objective(self) -> str:
        """Variants share the original objective ID before the hyphen."""
        return self.id.split('-')[0]


ROUNDS = {
    ('Smart Shopping', 'Middle school'): (
        Question('sm1', 'Which pack has the lower price for ONE pencil?',
                 ('4 for $2', '6 for $6', 'They cost the same'), 0, 'Unit prices',
                 'Divide each price by the number of pencils.',
                 'Pack A: $2 ÷ 4 = 50 cents each. Pack B: $6 ÷ 6 = $1 each. Pack A is the better deal.',
                 'Pencils for your school trip\n• Pack A: 4 pencils for $2\n• Pack B: 6 pencils for $6'),
        Question('sm2', 'Which bottle has the lower price for ONE liter?',
                 ('1 liter for $3', '2 liters for $4', 'They cost the same'), 1, 'Unit prices',
                 'For the big bottle, divide the price by 2.',
                 'The big bottle costs $4 ÷ 2 = $2 per liter. The small bottle costs $3 per liter. The big bottle gives more juice for each dollar.',
                 'Juice for your friends\n• Small bottle: 1 liter for $3\n• Big bottle: 2 liters for $4\nA liter measures how much juice you get.'),
        Question('sm3', 'What is the sale price?',
                 ('$2', '$10', '$8'), 2, 'Discounts',
                 'Work out the saving, then take it off the price.',
                 'You save $2. The bag costs $10 − $2 = $8. The saving and the price you pay are different amounts.',
                 'A bag for your trip\n• Normal price: $10\n• Sale: 20% off (save 20 cents per dollar)\n• No extra charges'),
        Question('sm4', 'Which cracker pack can you afford with the fruit?',
                 ('A $9 pack', 'A $6 pack', 'An $8 pack'), 1, 'Budgeting',
                 'Take the fruit cost away from your $12.',
                 'After buying fruit, you have $7 left. Only the $6 crackers fit. Fruit plus crackers costs $11.',
                 'Snack shopping\n• Money you can spend: $12\n• Fruit costs $5\n• You also want one pack of crackers\n• No extra charges'),
        Question('sm5', 'Which pack gets enough bars without spending too much?',
                 ('Buy 10 for $10', 'Neither pack fits', 'Buy 4 for $5'), 2, 'Budgeting',
                 'Check both the number of bars and the whole pack price.',
                 'The small pack has enough bars and costs $5. The big pack costs $10, more than you have, even though each bar is cheaper.',
                 'Snack bars for four friends\n• Money you can spend: $6\n• You need at least 4 bars\n• Small pack: 4 bars for $5\n• Big pack: 10 bars for $10'),
    ),
    ('Smart Shopping', 'High school'): (
        Question('sh1', 'Which bottle costs less for ONE liter?',
                 ('500 mL for $1.50', '2 liters for $4', 'They cost the same'), 1, 'Unit prices',
                 'Two half-liter bottles make one liter.',
                 'Two small bottles cost $3 for one liter. The big bottle costs $2 per liter. The big bottle is the better unit-price deal.',
                 'Juice for the trip\n• Small bottle: 500 mL for $1.50\n• Big bottle: 2 liters for $4\n• 500 mL is half a liter'),
        Question('sh2', 'Which deal saves more money?',
                 ('20% off', '$5 off', 'Both save the same'), 0, 'Discounts',
                 'Find 20% of $30 and compare that saving with $5.',
                 '20% of $30 is $6. That beats the $5 saving. You pay $24 with Deal A or $25 with Deal B.',
                 'Choose a bag deal\n• Normal price: $30\n• Deal A: 20% off\n• Deal B: $5 off\n• No extra charges'),
        Question('sh3', 'What do you pay after both discounts?',
                 ('$26', '$30', '$27'), 2, 'Discounts',
                 'Finish the first discount before working out the second.',
                 'The first discount makes the price $30. Then 10% of $30 is $3. You pay $27. You cannot simply add the two discount percentages.',
                 'Two discounts on a bag\n• Start price: $40\n• First: take off 25%\n• Next: take off 10% of the NEW price\n• No extra charges'),
        Question('sh4', 'What is the total including tax?',
                 ('$25', '$21', '$20.05'), 1, 'Budgeting',
                 'Find 5% of $20, then add it.',
                 'The tax is $1. The total is $20 + $1 = $21. A 5% tax does not mean a $5 charge.',
                 'Supplies for the trip\n• Price before tax: $20\n• Tax: 5% of the price\n• Tax is an extra charge added when you pay'),
        Question('sh5', 'Which store fits your spending limit?',
                 ('Store B', 'Store A', 'Both stores'), 0, 'Budgeting',
                 'Include delivery in the total price.',
                 'Store A costs $26 with delivery. Store B costs $24. Only Store B fits your $25 limit.',
                 'Buy supplies online\n• Money you can spend: $25\n• Store A: $19 plus $7 delivery\n• Store B: $24 with free delivery'),
    ),
    ('Spot the Scam', 'Middle school'): (
        Question('cm1', 'What should Sam do next?',
                 ('Pay to unlock the prize', 'Send it to more friends', 'Pause and ask a trusted adult'), 2, 'Verification',
                 'Why would a surprise prize ask you to pay?',
                 'Pause and ask a trusted adult to help check. A surprise prize asking for money is a warning sign. Do not pay or pass it on.',
                 'Pretend message to Sam\n“You won game coins! Send $5 to get your prize.”'),
        Question('cm2', 'What should Sam do with the password?',
                 ('Keep the password private', 'Share it just this once', 'Post it in the group chat'), 0, 'Privacy',
                 'A password is like the key to an account.',
                 'Keep the password private. Someone sending a gift does not need your password. Ask a trusted adult if the stranger keeps asking.',
                 'Pretend message from a stranger\n“Tell me your game password and I’ll send you a gift.”'),
        Question('cm3', 'How can Sam find out if this is true?',
                 ('Believe it straight away', 'Ask the teacher in the usual way', 'Ask the stranger for another link'), 1, 'Verification',
                 'Check with someone you already know at school.',
                 'Ask the teacher using the usual school app or in person. Another link from the stranger does not prove the message is true.',
                 'Pretend message from someone Sam does not know\n“The school trip is canceled!”'),
        Question('cm4', 'What should Sam do before believing the post?',
                 ('Believe it because it has likes', 'Buy the snack now', 'Look for proof from a trusted source'), 2, 'Evaluating claims',
                 'Lots of likes do not make a promise true.',
                 'Look for proof from a source you trust, and ask an adult for help. Big promises and lots of likes are not proof.',
                 'Pretend online post\n“Eat this snack and you’ll get every test answer right!”\nThe post gives no proof.'),
        Question('cm5', 'How can Sam check safely?',
                 ('Open the game’s official app directly', 'Click the message link', 'Reply with a password'), 0, 'Verification',
                 'Check the account without using the message link.',
                 'Open the official game app yourself. Do not use the surprise link or send your password. Ask a trusted adult if you are worried.',
                 'Pretend message to Sam\n“Click this link NOW or you’ll lose your game account!”'),
    ),
    ('Spot the Scam', 'High school'): (
        Question('ch1', 'What should Sam do BEFORE paying?',
                 ('Pay straight away', 'Ask the real organizer in the usual way', 'Share the message as true'), 1, 'Verification',
                 'A familiar name does not prove who sent a message.',
                 'Contact the real organizer through your usual school app or in person. Check the changed payment details before sending money.',
                 'Pretend message signed “School event organizer”\n“Pay the event fee right now! Use this new bank account.”'),
        Question('ch2', 'How should Sam check the account?',
                 ('Trust the logo', 'Reply with a sign-in code', 'Open the official app yourself'), 2, 'Verification',
                 'A scammer can copy a logo.',
                 'Open the official app or type the website address you already know. Do not use the message link. A familiar logo is not proof.',
                 'Pretend account warning\nThe message shows a familiar logo and says:\n“Use this link to sign in or your account will close.”'),
        Question('ch3', 'What would help Sam check the promise?',
                 ('Evidence from a source other than the seller', 'Lots of likes', 'The seller promising again'), 0, 'Evaluating claims',
                 'Look beyond what the seller says.',
                 'Look for evidence from people or sources separate from the seller. Paid adverts are not always wrong, but likes and promises do not prove they work.',
                 'Pretend advertisement\n“This study product guarantees top grades!”\nThe seller paid to promote this post.'),
        Question('ch4', 'What should Sam check before sharing it?',
                 ('How neat the screenshot looks', 'The original message and its date', 'How many friends shared it'), 1, 'Evaluating claims',
                 'A missing date or missing sentence can change the meaning.',
                 'Find the original school announcement. Check the date and full message. The screenshot could be old or missing an important correction.',
                 'Pretend screenshot in a group chat\nIt says a teacher canceled an event.\nPart of the message is cut off, and no date is shown.'),
        Question('ch5', 'What should Sam do with the code?',
                 ('Share it before it expires', 'Send half the code', 'Keep it private; contact official support'), 2, 'Privacy',
                 'Even a code that expires soon can unlock an account.',
                 'Keep the code private. Contact support through the official app instead. Never send a sign-in code to someone who asks in a message.',
                 'Pretend message from “Support”\n“Send us the sign-in code that just arrived on your phone.”\nThe code can unlock Sam’s account.'),
    ),
    ('Plan an Event', 'Middle school'): (
        Question('em1', 'Which room can you afford with the supplies?',
                 ('A $25 room', 'A $15 room', 'A $30 room'), 1, 'Event planning',
                 'Add the supplies to each room price.',
                 'The $15 room plus $10 supplies costs $25. That fits your $30 limit. The other rooms would make the total too high.',
                 'Plan a class party\n• Total money: $30\n• Supplies cost $10\n• You still need to pay for a room'),
        Question('em2', 'How much will all the snacks cost?',
                 ('$20', '$12', '$2'), 0, 'Event planning',
                 'You need ten snacks at $2 each.',
                 '10 × $2 = $20. The $2 price buys one snack, not snacks for the whole class.',
                 'Snacks for the class party\n• 10 students\n• One snack for each student\n• Each snack costs $2'),
        Question('em3', 'How much can you spend on the plan now?',
                 ('$60', '$50', '$40'), 2, 'Budgeting',
                 'Take the money you keep aside out of the total.',
                 'You can spend $50 − $10 = $40 now. The other $10 stays ready for an unexpected cost.',
                 'Plan party spending\n• Total money: $50\n• Keep $10 aside for surprises'),
        Question('em4', 'Which package costs less in total?',
                 ('Package A', 'They cost the same', 'Package B'), 2, 'Event planning',
                 'Add the materials cost before comparing.',
                 'Package A totals $23. Package B totals $20. Package B saves $3 because its materials are already included.',
                 'Choose a party activity\n• Package A: $18 plus $5 for materials\n• Package B: $20, with materials included\nBoth offer the same activity.'),
        Question('em5', 'How much money will you have left?',
                 ('$15', '$45', '$5'), 0, 'Budgeting',
                 'Add the three costs, then take that total away from $60.',
                 'The costs add up to $45. You have $60 − $45 = $15 left. The money spent is different from the money left.',
                 'Check the party plan\n• Total money: $60\n• Snacks: $20\n• Games: $15\n• Decorations: $10'),
    ),
    ('Plan an Event', 'High school'): (
        Question('eh1', 'What is the total cost?',
                 ('$32', '$70', '$60'), 1, 'Event planning',
                 'Find the cost for all twenty students, then add the room.',
                 'Supplies cost 20 × $2 = $40. Add the $30 room and the total is $70.',
                 'Plan a class celebration\n• Room: $30\n• 20 students\n• Supplies: $2 for each student'),
        Question('eh2', 'Which company costs less in total?',
                 ('Company B', 'Company A', 'Both cost the same'), 0, 'Event planning',
                 'Include the setup charge when comparing.',
                 'Company A costs $53. Company B costs $50, so B saves $3. The extra setup charge changes the comparison.',
                 'Choose a company for the celebration\n• Company A: $45 plus $8 to set up\n• Company B: $50, including setup\nBoth provide the same service.'),
        Question('eh3', 'How much do you pay?',
                 ('$20', '$75', '$60'), 2, 'Discounts',
                 '25% is one quarter. Find the saving, then subtract it.',
                 'One quarter of $80 is $20 saved. You pay $80 − $20 = $60.',
                 'Supplies on sale\n• Normal price: $80\n• Student discount: 25% off\n• No extra charges'),
        Question('eh4', 'How much can you put in the spending plan?',
                 ('$100', '$90', '$110'), 1, 'Budgeting',
                 'Work out the 10% you keep aside first.',
                 'Keep $10 aside. That leaves $90 for the plan. The extra money must come from your existing $100.',
                 'Make room for surprises\n• Total money: $100\n• Keep 10% aside for unexpected costs'),
        Question('eh5', 'What ticket price raises EXACTLY enough money?',
                 ('$3', '$2', '$4'), 0, 'Budgeting',
                 'Share the total cost equally across twenty tickets.',
                 '$60 ÷ 20 = $3 per ticket. At $2 you only raise $40. At $4 you raise $80, more than the exact cost.',
                 'Tickets for an optional activity\n• The activity costs $60 in total\n• All 20 student tickets will sell\n• Each ticket has the same price'),
    ),
}


def get_questions(challenge: str, level: str) -> tuple[Question, ...]:
    """Return a reviewed round or reject unsupported selections."""
    try:
        return ROUNDS[(challenge, level)]
    except KeyError as exc:
        raise ValueError('Choose a supported challenge and school level.') from exc


def question_bank(challenge: str, level: str, version: str) -> tuple[Question, ...]:
    """Resolve authored content without reinterpreting historical answer mappings."""
    original = get_questions(challenge, level)
    if version == '1':
        return original
    if version != CONTENT_VERSION:
        raise ValueError('Unsupported content version.')
    from kidspark.question_variants import EXTRA_QUESTIONS
    objectives = {q.id for q in original}
    return original + tuple(Question(*fields) for fields in EXTRA_QUESTIONS
                            if fields[0].split('-')[0] in objectives)


def select_questions(challenge: str, level: str, seed: str) -> tuple[Question, ...]:
    """Pick one variant per objective; keep the starter first and freeze the order."""
    rng = Random(seed)
    bank = question_bank(challenge, level, CONTENT_VERSION)
    selected = [rng.choice([q for q in bank if q.objective == original.id])
                for original in get_questions(challenge, level)]
    later = selected[1:]
    rng.shuffle(later)
    return (selected[0], *later)
