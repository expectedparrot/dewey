# **Chatbots for Data Collection in Surveys: A Comparison of Four Theory-Based Interview Probes** 

Rune M. Jacobsen Samuel Rhys Cox runemj@cs.aau.dk srcox@cs.aau.dk Aalborg University Aalborg University Aalborg, Denmark Aalborg, Denmark 

## **Abstract** 

Surveys are a widespread method for collecting data at scale, but their rigid structure often limits the depth of qualitative insights obtained. While interviews naturally yield richer responses, they are challenging to conduct across diverse locations and large participant pools. To partially bridge this gap, we investigate the potential of using LLM-based chatbots to support qualitative data collection through interview probes embedded in surveys. We assess four theory-based interview probes: descriptive, idiographic, clarifying, and explanatory. Through a split-plot study design ( _N_ = 64), we compare the probes' impact on response quality and user experience across three key stages of HCI research: _exploration_ , _requirements gathering_ , and _evaluation_ . Our results show that probes facilitate the collection of high-quality survey data, with specific probes proving effective at different research stages. We contribute practical and methodological implications for using chatbots as research tools to enrich qualitative data collection. 

## **CCS Concepts** 

- **Human-centered computing** -> _User studies_ ; **Empirical studies in HCI** . 

## **Keywords** 

Chatbots, Interview Probes, Online Surveys, Data collection 

### **ACM Reference Format:** 

Rune M. Jacobsen, Samuel Rhys Cox, Carla F. Griggio, and Niels van Berkel. 2025. Chatbots for Data Collection in Surveys: A Comparison of Four Theory-Based Interview Probes. In _CHI Conference on Human Factors in Computing Systems (CHI '25), April 26-May 1, 2025, Yokohama, Japan._ ACM, New York, NY, USA, 21 pages. https://doi.org/10.1145/3706598. 3714128 

## **1 Introduction** 

Online surveys are widely used in Human-Computer Interaction (HCI) research as a data collection method. They can reach a wide population [31], are cost-effective [85], and responses are quickly collected [21]. HCI research has extensively relied on online surveys to generate insights about users' attitudes, perceptions, habits, awareness, and experiences with technology [82]. Online surveys can provide both quantitative and qualitative self-reported data. For example, surveys often include a combination of closed-ended 

This work is licensed under a Creative Commons Attribution 4.0 International License. _CHI '25, Yokohama, Japan_ 

 2025 Copyright held by the owner/author(s). ACM ISBN 979-8-4007-1394-1/25/04 

https://doi.org/10.1145/3706598.3714128 

Carla F. Griggio Niels van Berkel cfg@cs.aau.dk nielsvanberkel@cs.aau.dk Aalborg University Aalborg University Copenhagen, Denmark Aalborg, Denmark 

questions with restricted response options, facilitating quantification and comparison [69], and open-ended questions for accessing richer, more detailed insights through respondents' own words [18, 94, 104]. 

However, the quality and richness of the qualitative data collected through online surveys is often more limited than when interacting with participants directly, such as when conducting face-to-face interviews. In surveys, any follow-up questions must be predetermined, potentially missing out on clarifying a vague answer or expanding on an interesting insight. Additionally, participant engagement may be less reliable [37, 52, 98, 125], resulting in low-quality [94] or nonsensical answers [39], or in omitting responses altogether. Beyond data quality, asking open-ended questions in surveys may cause survey fatigue [89], often ascribed to the cognitive load and the additional time and effort required, leading to _survey taking fatigue_ and participant dropout [91]. These limitations motivate the exploration of novel interactive methods for data collection that are capable of preserving the time- and costeffectiveness provided by online surveys without compromising on the richness and quality of open-ended answers. 

Recent research has explored the feasibility of collecting qualitative data through chatbots embedded in surveys, substituting open-ended questions with chatbot-based interview probes that interact with participants in a conversational style [40, 49, 63, 64, 121, 128, 131]. Chatbot-driven data collection in surveys has been shown to enhance participant disclosure [110, 127], improve data quality as compared to the traditional open-ended question format [63, 128], and been hypothesised to reduce satisficing behaviour [121]. However, chatbots often show limitations in understanding the diverse user input in responses to open-ended questions [26], leading to user disappointment and frustration [46]. With the recent surge of large-language models (LLMs), chatbot capabilities have taken a leap in their ability to interpret text and provide a sensible response, proposing a promising direction for utilising chatbots in surveys. 

We propose that LLM-based chatbots, instructed in conversational techniques based on face-to-face interviews, can facilitate the collection of high-quality qualitative data in surveys. A wellestablished approach to uncovering in-depth insights involves the use of interview probes, which aim to elicit richer and more nuanced insights based on participants' prior responses [41, 92, 97, 101]. Incorporating such probing techniques in chatbot-driven survey inquiries presents an opportunity to enhance data quality. However, interview probes can also negatively affect the interviewee's experience [14, 123]. This underscores the importance of carefully considering the survey-takers' experience when designing chatbots that employ probing questions. In this work, we are interested in exploring chatbot designs that can serve as tools for large-scale surveys to inform three common interview stages of HCI research 

CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Jacobsen et al. 

and practice [69, pp. 180-187]: Exploration, Reqirements, and Evaluation. To address these research gaps, we set out to answer two research questions: 

- **RQ1** _How can distinct chatbot-based interview probes support qualitative data collection across different interview stages of HCI research?_ 

- **RQ2** _What is the user experience of interacting with a chatbot-based interview probe when completing a survey?_ 

To address these research questions, we incorporate and assess four theory-based interviewing probes [97] in a chatbot for collecting high-quality qualitative data through online surveys. We examine the effectiveness of a Descriptive, Idiographic, Clarifying, and Explanatory interview probes in a between-subject setup across the common HCI research interview stages of Exploration, Reqirements, and Evaluation [69, pp. 180-187] in a within-subjects design. Our analysis focuses on assessing the impact of each interviewing probe on the quality of responses, using Gricean Maxims (a set of communication principles) to measure the informativeness, relevance, specificity, and clarity, as well as the participants' experience. 

We contribute an analysis of the effect of interview probes and research interview stages on response quality, as well as participant experience and perception of survey chatbots. Furthermore, we provide concrete recommendations for employing interview probes in HCI studies and outline opportunities and challenges for integrating LLM-based chatbots in surveys. Finally, we provide the source code and implementation details of our chatbot-based interview probes to support other researchers seeking to employ chatbots for data collection in surveys. 

## **2 Background and Related Work** 

## **2.1 Information Elicitation through Online Surveys** 

Conducting surveys is one of the primary methods for collecting insights into the opinions, experiences and perceptions of people [30]. In surveys, researchers and practitioners utilise a series of questions to elicit information on a topic of interest which is either closedor open-ended. Open-ended questions are crucial in collecting rich and nuanced data from participants [94], and in addition, attempt to uncover the _why_ of participant responses to closed-ended questions [18, 104]. Several factors can reduce the quality of responses to open-ended questions. This includes survey fatigue [89], where participants feel overwhelmed by the questions posed [68, 90] and either drop out or provide lower-quality responses by responding faster [91, 128]. Furthermore, answering open-ended questions is regarded as taking extra time and demanding increased effort due to the participant formulating their own words and typing out their responses [18]. These factors can lead to participants skipping this type of question or even providing gibberish responses [39]. In addition, researchers argue that it can be challenging to manage the progress of web surveys compared to in-person surveys [37, 52, 98], but that measurement errors are less prevalent when compared to surveys conducted in-person or over the phone. 

Researchers have introduced various techniques to counteract the drawbacks (such as reduced response quality) of open-ended questions. Web surveys have previously integrated lightweight 

probes, subtly modifying open-ended questions based on, for example, prior scale responses [6, 86]. In addition, researchers have created personalised surveys that incorporate prior participant data ( _e.g._ , social media and health trackers) into the formulation of survey questions [115]. In our work, we specifically focus on the systematic posing of follow-up questions based on immediate prior participant responses. 

## **2.2 Conversational AI and Chatbots** 

Introducing conversational elements as a means to elicit information has been explored in a variety of contexts, since conversational interfaces possess several advantages over traditional WIMP (Windows, Icons, Menus and Pointers) interfaces [76, 113], for instance, they do not lock users into a fixed path when users provide diverse requests [113]. This is why researchers and practitioners have deployed chatbots in myriad scenarios. For instance, customer service agents [16], tutoring students [42], planning and scheduling [24, 53, 78], recommending products, jobs or movies [59, 130], personal assistants [72], psycho therapy [102], group decision support [103], support in voting [34], workers companion [122]. Chatbots can enable gathering information from users both in general [93, 95, 114] and for specific tasks such as making recommendations [128], and for doing specific tasks [10]. 

In the context of surveys, prior work posits that chatbots can potentially improve the qualitative data collection process. This includes explaining the purpose of a question when asked by a participant and guiding them [71]. A chatbot has the ability to present survey questions as personalised, conversational messages, potentially enhancing participant involvement and the quality of their responses [51, 65]. Kim et al. found that, through satisficing theory, chatbots elicit higher quality responses compared to traditional surveys [63], which is supported by Xiao et al. [128], who furthermore found that a chatbot may increase participant engagement. Previous studies have shown that the social behaviours displayed by agents can successfully enhance user engagement across different social settings, as measured by indicators such as the duration of the interaction, the extent and depth of personal information shared, and a positive perception of the agent and the results of the interaction [9, 103]. In addition, participants have been found willing to share sensitive and personal information with a chatbot [109]. 

A key factor in utilising chatbots as part of web surveys is to evaluate their efficacy in eliciting information. The evaluation of conversational interfaces has traditionally been divided into two different directions, objective [29, 75, 117] and subjective metrics [4, 8, 55, 84]. Objective metrics are calculated directly from interaction logs and may include measures such as task or domain coverage, error rate, number of issues encountered during the interaction, accuracy, or similar metrics which can be benchmarked [29, 75, 117]. It may also include calculating task achievement, dialogue efficiency (such as duration and total number of exchanges), and dialogue quality ( _e.g._ , response time) [117]. Subjective metrics typically rely on user feedback regarding specific elements, such as satisfaction and comprehensibility ( _e.g._ , [55]). For HCI in particular, researchers have evaluated chatbot characteristics and behaviour such as anthropomorphism and likeability [4], ability to build rapport [8, 84], and trust [8]. 

CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Chatbots for Data Collection in Surveys 

In this work, we set out to utilise chatbots as interactive data collection in surveys, given their proven ability to improve data quality, participant engagement and disclosure. 

## **2.3 Interviewing Probes** 

Research interviews in social sciences have evolved notably over the past four decades, highlighted by significant contributions from Gorden [41], Mishler [80], Wengraf [118], Roulston [100], and Brinkmann and Kvale [12]. Probing, essential for uncovering rich, nuanced data, plays a key role in this evolution. Probing describes the asking of strategic follow-up questions that reveal deeper insights into participants' experiences, progressively uncovering potential hidden layers of participants' experiences or insights [92]. Gorden [41] and Bernard [101] have presented probing taxonomies. Gorden's six-probe framework aims to support interviewers eliciting comprehensive responses [41], ranging from silent and encouragement probes to more specific ones like elaboration, clarification, recapitulation, and reflective probes. Bernard built on this framework, including directive and baiting probes for eliciting more disclosure [101]. 

Recent work highlights the limitations of these frameworks [97], shedding light on several critical areas for improvement. One major critique involves the misuse of silence and encouragement as probes. While traditionally viewed as an effective strategy to elicit responses, silence can create discomfort or confusion, leading to less authentic participant responses. Encouragement probes, intended to motivate further discussion, may inadvertently introduce bias by signalling approval or disapproval. Additionally, Robinson [97] points out the omission of specific probe types like explanatory and idiographic probes in earlier frameworks. Explanatory probes are essential for understanding the reasoning behind participants' actions and thoughts, providing a deeper comprehension of their experiences. Idiographic probes, on the other hand, focus on capturing the unique, individual aspects of participants' experiences, which are often lost in more generalised probing strategies. Robinson [97] advocates for an updated probing framework that includes these overlooked probe types and offers a more comprehensive framework for interviewers. Such a framework, Robinson argues, should emphasise the theoretical underpinnings of each probe type, guiding interviewers to use them more effectively and appropriately in different contexts. In light of this, our paper adopts the four theory-based interviewing probes proposed by Robinson [97]. 

These probes are designed to capture a broad spectrum of participant experiences without leading the conversation. By grounding our probing strategy in established theory, we aim to enhance the quality and reliability of our findings. Table 1 provides examples of each of these four probes within an HCI context. We next describe each of these four probes in detail illustrating their theoretical foundations. 

_Descriptive Probe._ Descriptive probes derive from the Narrative Theory, which posits that individuals recount their lives through episodic narratives comprising both external actions and internal consciousness [13]. This theory underscores the co-construction of narratives, a concept introduced by Gorden [41] and expanded upon by Pasupathi [88], wherein narratives emerge collaboratively between the interviewer and interviewee. The descriptive probe encapsulates inquiring about both an individual's emotions, thoughts, and motivations during a recounted event as well as details about the surrounding circumstances, activities, and other people involved. 

_Idiographic Probe._ The idiographic probe, grounded in Autobiographical Memory Theory [11], is an interviewing technique used to elicit detailed and specific memories as opposed to generic and broad recollections. Autobiographical memory stores both types of memories: generic memories that summarise repeated experiences, and specific memories that contain rich, episodic details. Specific memories offer details and contexts, as stored in narrative-like structures that lend themselves to story-telling [19, 111]. Idiographic probing is a method that shifts an interviewee's recall from general to specific by requesting them to describe a single, detailed event that exemplifies a generic memory [99]. For example, an idiographic example-type probe might ask for a particular instance that reflects a frequently mentioned experience, thereby facilitating the cognitive transition into specific memory recollection [105, 111]. 

_Clarifying Probe._ The clarifying probe is a technique informed by Self-Disclosure Theory, which suggests that individuals share personal information in a layered fashion, contingent upon trust and intimacy levels with the listener [74]. As self-disclosure progresses, both the breadth and depth of the information shared increase, with breadth referring to the variety of topics and depth to the degree of detail and time spent on these topics [57, 119]. Clarifying probes play an important role in interviews, as they are designed to unpack earlier statements to reveal deeper, implicit meanings. By asking interviewees to expound upon a word or phrase, clarifying probes 

**Table 1: Hypothetical examples of the four interviewing probes within HCI.** 

|**Role**|**Descriptive**|**Idiographic**|**Clarifying**|**Explanatory**|
|---|---|---|---|---|
|Interviewer||_What is your experience wit_|_h technology in your life?_||
|Participant|_I b_|_elieve technology can do a lot of_|_good, but it can also be stressful._||
|Interviewer|_Can you describe in detail_<br>_what you were doing when you_<br>_felt stressed?_|_You said that technology can_<br>_be stressful, can you give me_<br>_a recent example of when you_<br>_experienced this?_|_You said technology can be_<br>_stressful, can you clarify what_<br>_that means to you?_|_Why do you believe that tech-_<br>_nology can be stressful?_|



CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Jacobsen et al. 

encourage the articulation of thoughts and emotions that might otherwise remain unvoiced. 

_Explanatory Probe._ Explanatory probes are informed by Attribution Theory, which explores how individuals discern the causes of events in their lives. The theory proposes that people attribute causes to events based on a range of factors [61]. These attributions are subjective and influenced by cognitive biases, yet they significantly impact emotions and behaviours. Therefore, understanding the perceived causes behind actions and events is crucial to grasp the narrative sense-making processes that individuals employ. Explanatory probes solicit personal insights into the reasons behind occurrences or feelings. Researchers can use these probes to uncover narrative attributions that participants make regarding the occurrence of certain phenomena [112]. These probes are particularly useful when the understanding of perceived causality is of interest and can help make sense of autobiographical stories. 

## **3 Survey Chatbot** 

We designed and implemented a chatbot with the goal of collecting in-depth qualitative data in online surveys. Specifically, we investigate four distinct interviewing probes [97], as detailed in Section 2.3, in the context of three stages of HCI inquiry [69, pp. 180-187]. We implemented the chatbot as a stand-alone application developed in Nextjs. The chatbot is running on a university server and integrates into already established survey platforms as an HTML iframe element [116]. This allows for the survey platform to save the data directly alongside the other collected survey data. 

_Chat Interface._ We have purposefully designed the chat interface to follow simple and minimalistic design considerations (see Fig. 1), as both colours [2, 17, 45, 50] and the introduction of avatars [20, 36, 67, 73, 106] can influence the user experience and perception of a chat conversation. The design follows a conventional text-based 

instant messaging approach, with a list of message bubbles and an input area at the button with a submit button. The label above each message signifies the sender, in our case: _chatbot_ and _you_ . We implemented this tool from scratch to enable customisations dedicated to specific research needs, avoid potential limitations of existing libraries, and allow potential future adopters to more easily grasp and control the system's functionality. 

_LLM & Prompt Architecture._ The chatbot is based on OpenAI's gpt4o model (gpt-4o-2024-05-13) which is instructed through elaborate prompt engineering. The prompt architecture for the chatbot is divided into four discrete parts: 

- (1) **General Instructions** --- This prompt instructs a chatbot to conduct interviews on technology-induced stress, asking one concise question at a time and acknowledging responses neutrally. 

- (2) **Topic of Interest** --- This prompt provides a comprehensive summary of technologically induced stress (elaborated in Section 4.2). The goal is to provide the chatbot with a reference for establishing the follow-up questions. 

- (3) **Interview Stage** --- This prompt describes the interview stages of HCI research (elaborated in Section 4.1). By explaining through the prompt the motivations and goals of each stage the chatbot may adapt the questions to match the current stage. The prompt is being switched according to which stage the chatbot is inquiring into ( _i.e._ , exploration, requirements gathering, or evaluation). 

- (4) **Interview Probe** --- Finally, we provide the bot with a prompt describing the specific interview prompt in detail, including example questions. This prompt instructs the chatbot to follow a specific procedure when inquiring in greater detail based on what participants have already disclosed. This prompt is likewise switched around. 



<!-- Start of picture text -->
CHATBOT<br>Hello, I would like to discuss the impact of technology on stress.<br>Have you experienced technology having a stressing effect on your<br>life?<br>YOU<br>Yes, I feel as if I can never get a "break".  My phone is always on<br>and I always get messages or emails or even calls.  When I think<br>about it, It gives me anxiety because I never know what else is<br>going to pop up<br>CHATBOT<br>Thank you for sharing that. Can you recall a specific time when you<br>felt particularly overwhelmed by these notifications and messages?<br>What exactly happened during that time?<br>YOU<br>I wasnt feeling well and just wanted to relax and try to clear my<br>mind.  But my phone kept going off because I guess everyone in<br>the world at the moment wanted something from me<br>CHATBOT<br>I understand. Can you describe what you did in response to your<br>phone constantly going off during that time? How did it affect your<br>attempts to relax and clear your mind?<br>I answered a couple of messages and then ended up throwing my phone away from me so that I wouldnt be bothered by it SEND<br><!-- End of picture text -->

**Figure 1: Chatbot interface with a conversation from our study in exploration stage with the idiographic interview probe.** 

CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Chatbots for Data Collection in Surveys 

## **4 Method** 

We set out to systematically investigate the effects of four distinct interviewing probes on participant responses in conversational surveys. We investigate this effect across different stages of interviews, reflecting distinct interview goals within HCI. We structured the study using a 4 (interview probes) x 3 (stages of interview) mixed design ( _i.e._ , split-plot design). This design allows us to assess the impact of specific probes on the distinct interview stages, reflecting contemporary real-world HCI practice (RQ1). Our split-plot design ensures that participants experience the same interview probe over different interview stages, providing insights across stages while limiting participant load and fatigue. We manipulated the interview stage as a within-subjects variable, with each participant experiencing all three interview stages. Conversely, we treat the interview probe as a between-subjects variable, with each participant interacting with only one out of the four interview probes throughout the entire study. All participants focused on the topic of stress related to technology use for the survey. Additionally, we investigate the user experience of interacting with an LLM-based chatbot to answer qualitative survey questions through standardised and custom Likert-scales (RQ2). 

## **4.1 Interview Stages** 

Interviews are employed to aid researchers in establishing an understanding of the " _needs, practices, concerns, preferences, and attitudes_ " of users towards a current or future technology system [69]. We follow the distinctions of three applications of interviews within HCI by Lazar et al.: Exploration, Reqirements, and Evaluation [69, pp. 180-187]. For clarity, we use the term interview stages in the context of this paper. Exploration focuses on understanding users' experiences, needs, and preferences involving current or future technologies. This method gathers insights into users' daily practices, aspirations, and challenges with current tools. Reqirements involves interviewing users to understand their needs, goals, and frustrations within the context of interest with the goal of establishing a set of requirements for future technologies or changes in existing technologies. Evaluation is used to gather feedback on prototypes and completed products, crucial for refining design and functionality. Evaluation interviews help validate design decisions and identify areas for improvement by capturing user feedback. While we utilise three distinct stages of interviews within HCI, we recognise that the different activities can potentially overlap and often occur in an iterative process. 

## **4.2 Technology Stress as a Case** 

For this particular study, we investigate the case of stress related to, or induced by, the adoption and use of technology [1, 3]. In HCI, this phenomenon (also referred to as _technostress_ [27, 66, 96], and _technophobia_ [47, 62]) has emerged as a significant area of concern [15, 33]. Technology stress concerns the stress or psychological discomfort experienced by individuals due to their inability to adapt or cope with information and communication technologies in a healthy manner. This condition is triggered by the pervasive integration of digital technologies into both our personal and professional lives [77], potentially leading to a state of connectivity 

that individuals find challenging to manage effectively. Both the absence and presence of technology can be a stressor in people's everyday and working lives [83]. The case represents a complex and pertinent area of inquiry holding both apparent and tacit participant knowledge with both explicit and implicit dimensions, making it suitable for investigation in our study. 

In our study, all participants went through all three stages of interviews in HCI (Exploration, Reqirements, and Evaluation). We presented an introduction to the specific task alongside a visual aid (see Appendix A.1 for task descriptions and images/video), followed by participants interacting with the chatbot as per one of the four interviewing probes. In Exploration, we showed participants images of everyday activities regarding technology, spanning pictures from private, public, and work contexts in order to provide relatable examples for participants to reflect on their own experiences. In Reqirements, we likewise showed the participants pictures of everyday situations however this time the pictures was with focus on technology in use. Furthermore, the text explicitly stated the goal of setting requirements for interventions into existing or future use of technology. In Evaluation, the participants watched an introduction video for Apple's ' _do not disturb_ '-feature for an iOS-based device. In this case, the goal was to elicit particular reflections on a technology's ability to support a user's technologically induced stress. After the preparation step, the user interacted with the chatbot. For each step, the participant was instructed to continue the conversation as long as they had something they were willing to share on the matter. As there are no clear conventions on how to terminate conversations with a chatbot, we instructed participants to send a message saying 'goodbye' to the chatbot in order to proceed to the next part of the survey. 

## **4.3 Participants** 

Participants were recruited through Prolific, an online crowdsourcing market for research. We restricted participation to those in the participant pool with an acceptance rate above 95%, based in the USA and with the primary language of English. We limited participation to participants using a desktop computer, as extended typing on a mobile phone can be tiresome and to avoid potential usability issues with the chatbot on a small screen<sup>1</sup> . We compensated participants with a fixed amount of $3 for an estimated completion time of 15 minutes. To minimise type II errors, we determined our sample size based on a power calculation using G*Power [32]. Considering the exploratory nature of our study, we followed established methodological guidelines [48], using medium-to-large effect sizes _f_<sup>2</sup> = 0 _._ 2, an alpha level of 0.05, and a power of 0.8. This resulted in a minimum sample of 64 participants (16 in each split-plot). We set up four different Prolific studies ( _i.e._ , one for each interview probe), with a restriction ensuring that a participant can only participate once across all four studies. As such, each group were randomly sampled from the Prolific participant pool matching the restrictions. After accepting the study, the participants were then routed to Qualtrics for survey completion. 

> 1In Prolific, we indicated that the study should be taken on desktops only: https: //researcher-help.prolific.com/en/article/9c108d, and we further restricted the participation through Qualtrics: https://www.qualtrics.com/support/survey-platform/surveymodule/question-options/display-logic/. 

CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Jacobsen et al. 

## **4.4 Measures** 

We collect three sets of measures for our study. First, we evaluate the quality of participant responses both computationally and with manual labelling. Second, we measure participants' experiences and perceptions of the chatbot through both standardised and custom Likert-scales. Finally, we ask participants open-ended questions about the chatbot's way of asking questions and their preferences for providing qualitative data in online surveys. 

_Response Quality._ To assess the quality of the participants' responses we build on the work of Xiao et al. [128], which introduced the concept of Gricean Maxims to measure the informativeness, relevance, specificity, and clarity of participant responses. Proposed by H.P. Grice in 1975 [43, 44], Gricean Maxims are described as " _cooperative principles to guide effective communications_ " [28]. We adopt the Gricean Maxim implementation as proposed by Xiao et al. [128] to measure and calculate the participants' response quality. They propose to create proxies for each quality measure which allow for the quantification of each principle, which are defined as _informativeness_ , _specificity_ , _relevance_ and _clarity_ . Unlike Xiao et al. [128], we considered every response as we are not only interested in the combined responses, but each response individually. We consider each message as a response to a probing question. This is why we filter out the first response from each condition, as they are not the direct results of a probe. We did not only analyse the individual responses but also each Gricean Maxim in relation to the questions asked and the context. Hence, aiming to provide a focused analysis of the impact of each interview probe. For instance, regarding relevance, a question from the chatbot may be phrased as a "how do you think question", but it is answered by listing stressing technologies without providing an explanation -- hence focusing on the _what_ rather than the _how_ leading to a response of lower relevance. 

According to the Gricean Maxim of quantity, effective communication should be informative. We calculated the _informativeness_ of text responses [56] using the sum of each word's surprisal, defined as the inverse of its frequency in modern English. Lower-frequency words convey more information. We averaged word frequencies across four text corpora---the British National Corpus [70], The Brown Corpus [54], Web Text Corpus [87], and the NPS Chat Corpus [35], again following Xiao et al. [128])---to estimate a word's commonness in modern English and subsequently assessed the total informativeness of participants' responses to open-ended questions based on this metric. 

While our informativeness metric quantifies the amount of information in a user's text response, it does not evaluate the _specificity_ 

of the response. Specific responses, which provide detailed information, aid researchers in understanding and leveraging the data, and offer deeper insights. Given the variability and complexity of responses to open-ended questions, we manually rated each response's specificity on a three-point scale: 0 for generic descriptions, 1 for specific concepts, and 2 for specific concepts with detailed examples. 

According to the Gricean Maxim of _relevance_ , quality communication must be pertinent to the context. In surveys, responses should directly address the posed question. Irrelevant responses not only lack value but also complicate analysis. Given the diversity and complexity of responses to open-ended questions, we manually evaluated their relevance on a three-point scale: 0 for irrelevant, 1 for somewhat relevant, and 2 for fully relevant. 

Finally, according to the Gricean Maxim of _clarity_ , effective communication should be clear and easily understood without ambiguity. We assessed the clarity of each text response on a three-level scale: 0 for illegible text, 1 for incomplete sentences or grammatical errors that hinder understanding, and 2 for clearly articulated responses with complete sentences and no significant grammatical issues. 

For the metrics, _specificity_ , _relevance_ and _clarity_ , we provide examples in Appendix A.2 on the scoring of text responses on the three-point scale. Our labelling process involved two researchers initially coded a random 10% of the dataset blind to which interview probe was used. The two authors were intentionally aware of the research stage to be able to evaluate whether a response was considered of good quality and in line with the goals in the research stage. Following this, the two authors met and compared the labelled responses and resolved any differences by critically evaluating the criteria and arguments for every label of a response. After every response label was settled, the first author labelled the remainder of the dataset. 

_Subjective Experience._ We measure the participants' subjective experience of interacting with the chatbot by asking them to answer a set of Likert-scale questions (see Table 3). First, we utilise the _smoothness_ -scale of the standardised Session Evaluation Questionnaire (SEQ) [108], which is scored on five Likert-style questions ranging from 1--7 (see Appendix A.3 for dimension calculations, and [107] for instructions). In recent work, SEQ has been used to measure the experiences of users interacting with chatbots in HCI [7]. Second, we ask the participant to rate the chatbot on four Likert-point scales whether they experienced the chatbot as _helpful_ [129], _useful_ [129], _repetitive_ , and _intrusive_ . Finally, we ask the participants to rate on a 7-point Likert-scale if the things they revealed to the chatbot during the three sessions are accurate reflections on their personal thoughts, feelings, and experiences [58, 120]. 

**Table 2: Gricean Maxim for analysing conversation quality in conversational surveys, as based on Xiao et al. [128].** 

|**Maxim**|**Definition**|**Quality Metric**|**Definition**|
|---|---|---|---|
|**Quantity**|One should be as informative as possible|_Informativeness_<br>_Specificity_|A participant's response should be as informative as possible<br>A response should be as detailed as possible|
|**Relevance**|One should provide relevant information|_Relevance_|A participant's response should be relevant to a question asked|
|**Manner**|One should communicate in a clear and<br>orderly manner|_Clarity_|A participant's response should be clear|



CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Chatbots for Data Collection in Surveys 

**Table 3: Overview of the Likert-scales for measuring subjective experience** 

|**Measure**|**Question**|**Scale**|**Ref.**|
|---|---|---|---|
|SEQ|My conversations with the chatbot were...: <Difficult-Easy>, <Relaxed-Tense>, <Unpleasant-Pleasant>,<br><Rough-Smooth>, and <Comfortable-Uncomfortable>|1--7|[108]|
|Helpful|As an interviewee, I perceived the chatbot's questions as: Helpful <Strongly Disagree-Strongly Agree>|1--7|[129]|
|Useful|As an interviewee, I perceived the chatbot's questions as: Useful <Strongly Disagree-Strongly Agree>|1--7|[129]|
|Repetitive|As an interviewee, I perceived the chatbot's questions as: Repetitive <Strongly Disagree-Strongly Agree>|1--7||
|Intrusive|As an interviewee, I perceived the chatbot's questions as: Intrusive <Strongly Disagree-Strongly Agree>|1--7||
|Accuracy|The things that I revealed to the chatbot are accurate reflections of my personal thoughts, feelings and<br>experiences <Strongly Disagree-Strongly Agree>|1--7|[58, 120]|



_Post-study Open-ended Questions._ At the end study, we asked the participants four open ended questions in two parts. First, to better understand the participants' experiences and perceptions of the chatbot itself, we asked them to describe their experiences with the chatbot's line of questioning and the chatbot's questioning style. Second, to understand the use of chatbots as part of surveys, we asked the participants to compare their experience of responding to questions from a chatbot compared to traditional open-ended questions, thereby drawing from the participants' vast experience as frequent survey participants. We also asked the participants whether there are any topics that they would rather disclose to a chatbot than a human, or vice versa. We asked the following questions: 

- Please describe your experience with and perceptions of the chatbot's line of questioning. For example how the chatbot's questions affected your answers. 

- How would you describe your perceptions of the chatbot's questioning style? Please consider the variety, relevance, and impact of the questions asked. 

- How does your experience of talking to the chatbot compare to responding to traditional open-ended surveys? Please describe specific drawbacks or benefits. 

- Are there any topics that you would rather disclose to a chatbot than to a human, or vice versa? Please motivate why / why not. 

## **4.5 Data Analysis** 

_Response Quality._ To investigate the effect of our independent variables (interview probe and interview stage) on the quality measures of _informativeness_ , _relevance_ , _specificity_ , and _clarity_ , we constructed a mixed model for each of the four quality measures. We conducted an iterative construction of each of the models through incremental removal of variables based on their predictive power and Akaike information criterion (AIC), including number of messages, age, and gender of the participants, as well as duration of interaction. Our final set of predictors consisted of the two independent variables, interview probes and interview stages, for all models. As we include each individual response in our models, we included participant ID as a random effect in all four models to account for variance between participants, mitigating inflated Type I errors due to non-independence of observations. The informativeness model was constructed and evaluated using the R package lme4 [5], and the relevance, specificity, and clarity models were constructed as Cumulative Link Mixed Models due to their ordered ordinal data. 

_Subjective Experience._ To analyse the multivariate Likert data (chatbot experience, smoothness, and accuracy), we employed the Aligned Rank Transform (ART) method as proposed by Wobbrock et al. [124], using the ARTool R package. ART is well-suited for nonparametric data, while preserving the assumptions of traditional parametric tests. We investigated the effects of the independent variable _interview probe_ . Subsequently, we performed pairwise _t_ -tests to assess the significance of these variables, applying Bonferroni correction to adjust for multiple comparisons. 

_Analysis of Post-study Open-ended Questions._ We grouped the answers to the four open-ended questions into two categories: one for experiences and perceptions of questioning style, and the other for opinions on chatbots in surveys. We then looked for the most salient patterns in the answers of each group following an inductive approach [69, pp. 285-299]. The first author annotated the data with an initial set of codes in a spreadsheet, which was then refined in discussion with another author. Continuing this, the first author wrote a summary of the most salient patterns, which were further discussed and iterated with the rest of the authors. 

_Exploratory Conversation Analysis._ As part of our investigation into open-ended textual conversations between survey participants and a chatbot, we sought to assess emerging conversational patterns. The first author reviewed the conversation history for each participant, identifying communication and interaction patterns which were then discussed with the co-authors, with the most significant interactions selected and exemplified. Through iteration, we selected a final set of five distinct patterns. This exploratory analysis was not intended to generate generalisable claims, but rather to highlight unique aspects of the conversations that could deepen our understanding of participant-chatbot interactions and inspire future designs. 

## **5 Results** 

We report the results of our study, which compared four theorybased interview probes across three stages of HCI research. A total of 64 participants (16 per split-plot), evenly divided by gender (32 male, 32 female) and ranging in age from 19 to 67 years ( _M_ = 38 _._ 67, _SD_ = 12 _._ 31), took part in the study. The participants generated 1,287 responses to the interview probe questions across all conditions (see Table 4 for the distributions). In this section, we first present the findings related to quality measures across all conditions. Next, 

CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Jacobsen et al. 

**Table 4: Messages sent across conditions.** 

||**Exploration**|**Requirements**|**Evalu**|**ation**|
|---|---|---|---|---|
|**Descriptive**|114 (_M_= 8_._14)|115 (_M_= 7_._19)|88 (_M_|= 7_._19)|
|**Idiographic**|115 (_M_= 7_._67)|69 (_M_= 4_._6)|44 (_M_|= 2_._93)|
|**Clarifying**|162 (_M_= 10_._1)|97 (_M_= 6_._93)|79 (_M_|= 5_._27)|
|**Explanatory**|190 (_M_= 11_._9)|141 (_M_= 8_._81)|73 (_M_|= 5_._62)|



we provide insights into participants' perceptions and experiences of interacting with the chatbot. Third, we explore qualitative feedback regarding the chatbot's questioning style and its potential use in surveys. Finally, we offer exploratory insights into interesting patterns in the interactions participants had with the chatbot. 

## **5.1 Assessing Response Quality** 

We used a likelihood ratio test for comparing each model to its respective null model, which shows that our logistic regression models are all statistically significant; informativeness ( __<sup>2</sup> (11) = 40.412, _p_ < .001), relevance ( __<sup>2</sup> (11) = 48.928, _p_ < .001), specificity ( __<sup>2</sup> (11) = 71.035, _p_ < .001), and clarity ( __<sup>2</sup> (11) = 86.451, _p_ < .001). The informativeness model explains 45.8% of the variance in our model (R = 0.68, R<sup>2</sup> = 0.46), the relevance model 28.2% (R = 0.53, R<sup>2</sup> = 0.28), the specificity model 28.4% (R = 0.53, R<sup>2</sup> = 0.28), and the clarity model 33.9% (R = 0.58, R<sup>2</sup> = 0.34). We tested for the existence of multicollinearity among the models' parameters and found a variation inflation factor (VIF) between 1.65 and 5.11 for the predictors of the informativeness model, between 1.89 and 5.57 for the relevance model, between 1.87 and 5.09 for the specificity model, and between 

1.80 and 5.10 for the clarity model. These values are all below the often-used threshold of ten to detect multicollinearity [48]. We now present the significant predictors of all four models. Outcomes for all models are summarised in Table 5. 

_Interview Probe._ In this section, we present the main effects of interview probe type on the four quality measures (see Figure 1). For relevance, we find that the Explanatory probe provides significantly less relevance compared to the Idiographic probe ( __<sup></sup> = -2 _._ 1000, _SE_ = 0.425, _p_ < 0.0001) and the Clarifying probe ( __<sup></sup> = -1 _._ 1972, _SE_ = 0.429, _p_ = 0.0270). In terms of specificity, the Explanatory probe elicited significantly less specific responses compared to the Descriptive probe ( __<sup></sup> = 1 _._ 053, _SE_ = 0.391, _p_ = 0.0358) and the Idiographic probe ( __<sup></sup> = -1 _._ 714, _SE_ = 0.397, _p_ = 0.0001). Regarding clarity, both the Clarifying and Explanatory probes result in notably lower scores as compared to the Descriptive and Idiographic probes, suggesting that these two probe types might be less effective in prompting clear responses. Regarding clarity, the Explanatory probe resulted in significantly lower scores compared to both the Descriptive probe ( __<sup></sup> = 1 _._ 619, _SE_ = 0.515, _p_ = 0.0092) and the Idiographic probe ( __<sup></sup> = -2 _._ 738, _SE_ = 0.524, _p_ < 0.0001). The Clarifying probe also scored significantly lower than the Idiographic probe ( __<sup></sup> = -1 _._ 724, _SE_ = 0.524, _p_ = 0.0055). Finally, for informativeness, we find no significant differences between the four probes. 

_Interview Stage._ Next, we present the main effects of interview stage type on the four quality measures (see Figure 2). For informativeness, the Explorationstage scored significantly higher than both 

**Table 5: Generalised linear models of the four quality measures. For each predictor, we report coefficients, standard errors (in brackets), and significance indicators. The sign of the estimate (+/-) denotes the direction of the relationship between the predictor and outcome variable (informativeness, relevance, specificity, and clarity).** 

|**Predictor**|**Inform**|**ativeness**|**Rel**|**evance**|**Spei**|**cificity**|**Cl**|**arity**|
|---|---|---|---|---|---|---|---|---|
|**_Baselines:_**|||||||||
|**_Probe = Descriptive, Interview Stage = Expl_**|**_oration_**||||||||
|**Interview Probe**|||||||||
|Idiographic|32.95|(52.02)|0.24|(0.48)|0.21|(0.21)|0.23|(0.48)|
|Clarifying|-65.90|(51.37)|-0.99|(0.48)*|-0.20|(0.43)|-0.99|(0.46)|
|Explanatory|-71.62|(50.87)|-1.46|(0.46)**|-1.30|(0.43)**|-1.46|(0.46)**|
|**Interview Stage**|||||||||
|Requirements|-14.10|(-14.10)|-0.36|(0.29)|-0.70|(0.28)*|-0.36|(0.29)|
|Evaluation|-64.02|(-64.02)**|-1.04|(0.29)***|-1.19|(0.28)***|-1.03|(0.30)|
|**Interaction effects**|||||||||
|Probe (Idiographic) : Stage (Requirements)|-15.29|(-15.29)|1.07|(0.44)*|0.24|(0.36)|1.06|(0.44)*|
|Probe (Clarifying) : Stage (Requirements)|5.58|(5.58)|1.08|(0.41)**|-0.31|(0.38)|1.07|(0.40)**|
|Probe (Explanatory) : Stage (Requirements)|-52.75|(-52.75)|0.08|(0.38)|-0.11|(0.36)|0.08|(0.38)|
|Probe (Idiographic) : Stage (Evaluation)|35.58|(35.58)|1.54|(0.49)**|1.08|(0.46)*|1.54|(0.50)**|
|Probe (Clarifying) : Stage (Evaluation)|22.57|(22.57)|1.61|(0.42)***|-0.07|(0.40)|1.61|(0.42)***|
|Probe (Explanatory) : Stage (Evaluation)|-8.39|(-8.39)|1.32|(0.42)**|0.87|(0.40)*|1.32|(0.42)**|



**** _p_ < 0.001, ** _p_ < 0.01, * _p_ < 0.05 

CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Chatbots for Data Collection in Surveys 



<!-- Start of picture text -->
Informativeness Relevance Specificity Clarity<br>3 20 20 20<br>2 ---------. 8 2<br>z5 ae Fi ---; ae ------ae ae =;---_-_---_<br>= 200|-f of 3 i i 3 oe E fy :<br>3 $0  1 Boe Grol k $ S10<br>3 = = ' 8<br>B3 p00 foreseenBHas ennnninenesrnnnin3H 9p vonnnineee wove Bos}E .<br>aa<br>oeospociE08G0 agost oeengosB Aco 9859 esgod oeFoswegos gioFei?E08ap csaod oegs?og 5 gta0coig6 aod<br><!-- End of picture text -->

**Figure 1: Visualisation of the interview probe main effects for each quality measure.** 

the Evaluation ( __<sup></sup> = 51 _._ 6, _SE_ = 12.0, _p_ = 0.0001) and Reqirements stages ( __<sup></sup> = 29 _._ 7, _SE_ = 10.7, _p_ = 0.0154), indicating that responses in the Exploration stage were more informative compared to the other stages. The Evaluation stage had a significant negative effect on relevance compared to the Exploration stage ( _p_ < 0.001). However, post-hoc comparisons did not find significant differences between the stages, suggesting that the stage effect alone may not be strong. For specificity, both the Reqirements ( __<sup></sup> = 0 _._ 7448, _SE_ = 0.137, _p_ < 0.0001) and Evaluation stages ( __<sup></sup> = 0 _._ 7215, _SE_ = 0.155, _p_ < 0.0001) produced significantly less specific responses compared to the Exploration stage. Finally, no significant differences were observed between the three interview stages in terms of clarity, suggesting that the clarity of responses remained consistent across all stages. 

_Interaction between Probe and Stage._ Next, we present the results of the interaction effects between the interview probe and interview stage in order to investigate each probe's usefulness within each stage of HCI research. Specifically, we further analyse each significant predictor through a pairwise comparison with Tukey p-value correction. We report how the individual probes compare 

to each other based in a particular interview stage. We visualise all interaction effects in Figure 3. 

_Interaction between Probe and Stage for Exploration._ We now present the significant results of the pairwise comparisons of interview probes for the Exploration stage. We provide means and standard deviation for each measure and probe in Table 6. No significant differences were observed between the probes for informativeness. For relevance, the Descriptive probe scored significantly higher than the Explanatory probe ( __<sup></sup> = 1 _._ 4608, _SE_ = 0.459, _p_ = 0.008). The Idiographic probe scored significantly higher than the Clarifying probe ( __<sup></sup> = -1 _._ 2264, _SE_ = 0.463, _p_ = 0.040), and the Idiographic probe also scored significantly higher than the Explanatory probe ( __<sup></sup> = -1 _._ 7007, _SE_ = 0.456, _p_ = 0.001). For specificity, the Descriptive probe performed significantly better than the Explanatory probe ( __<sup></sup> = 1 _._ 303, _SE_ = 0.430, _p_ = 0.0131), and the Clarifying probe also outperformed the Explanatory probe ( __<sup></sup> = 1 _._ 099, _SE_ = 0.414, _p_ = 0.0399). Additionally, the Idiographic probe performed better than the Explanatory probe ( __<sup></sup> = -1 _._ 519, _SE_ = 0.429, _p_ = 0.0023). Finally, we found no significant differences for clarity. 



<!-- Start of picture text -->
Informativeness Relevance Specificity Clarity<br>H8a<br>5<br> ---.. 815 15 ws ot<br>= 20 t t 23 z z i ca3 i= 35 z z 3<br>32<br>3B05 05 . . o Bos . . .<br>&3 &5 ri&E Fa<br>OF co  BF s OF co BF co ays<br>ow ho oo eno of (wo oo<br><!-- End of picture text -->

**Figure 2: Visualisation of the interview stage main effects for each quality measure.** 

CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Jacobsen et al. 



<!-- Start of picture text -->
Informativeness Relevance Specificity Clarity<br>00 20 20 20 panting<br> 200}..---4 = Pr] eee ene | , a5 feos Foe 45 { t<br>8 100 os os a os<br>ooooo "eoeo aw ron< oose wr ooe eohno aw ot oeNad co"o<br>es  oP oes'  ooo  aoa e<br>* Descriptive  Idiographic * Clarifying  Explanatory<br><!-- End of picture text -->

**Figure 3: Visualisation of the interaction effects between interview stage and interview probe main for each quality measure.** 

_Interaction between Probe and Stage for Requirements Gathering._ We now present the significant results of the pairwise comparisons of interview probes for the Reqirements stage. We provide means and standard deviation for each measure and probe in Table 6. For informativeness the Idiographic probe outperformed the Explanatory probe ( __<sup></sup> = -142 _._ 02, _SE_ = 52.8, _p_ = 0.0421). For relevance, the Clarifying probe scored significantly higher than the Explanatory probe ( __<sup></sup> = 1 _._ 4717, _SE_ = 0.474, _p_ = 0.0103), and the Descriptive probe also outperformed the Explanatory probe ( __<sup></sup> = 1 _._ 3786, _SE_ = 0.471, _p_ = 0.0180). The Idiographic probe scored significantly higher than the Explanatory probe ( __<sup></sup> = -2 _._ 6851, _SE_ = 0.504, _p_ < 0.0001). For specificity, the Descriptive probe outperformed the Explanatory probe ( __<sup></sup> = 1 _._ 419, _SE_ = 0.448, _p_ = 0.0084), and the Idiographic probe also performed better than the Explanatory probe ( __<sup></sup> = -1 _._ 885, _SE_ = 0.466, _p_ = 0.0003). And finally, for clarity, the Descriptive probe outperformed the Explanatory probe ( __<sup></sup> = 1 _._ 3786, _SE_ = 0.471, _p_ = 0.0180), and the Clarifying probe also performed better than the Explanatory probe ( __<sup></sup> = 1 _._ 4717, _SE_ = 0.474, _p_ = 0.0103). Additionally, the Idiographic probe outperformed the Explanatory probe ( __<sup></sup> = -4 _._ 0268, _SE_ = 0.614, _p_ < 

0.0001), the Descriptive probe ( __<sup></sup> = -1 _._ 9912, _SE_ = 0.583, _p_ = 0.006), and the Clarifying probe ( __<sup></sup> = -1 _._ 9135, _SE_ = 0.612, _p_ = 0.001). 

_Interaction between Probe and Stage for Evaluation._ We now present the significant results of the pairwise comparisons of interview probes for the Evaluation stage. We provide means and standard deviation each measure and probe in Table 6. The informativeness score the Idiographic probe outperformed the Explanatory probe ( __<sup></sup> = -148 _._ 53, _SE_ = 55.8, _p_ = 0.0441). For relevance, the Idiographic probe scored significantly higher than the Descriptive probe ( __<sup></sup> = -1 _._ 7753, _SE_ = 0.558, _p_ = 0.0080) and also scored significantly higher than the Explanatory probe ( __<sup></sup> = -1 _._ 9142, _SE_ = 0.559, _p_ = 0.0035). For specificity, the Idiographic probe outperformed both the Clarifying probe ( __<sup></sup> = -1 _._ 577, _SE_ = 0.521, _p_ = 0.0132) and the Explanatory probe ( __<sup></sup> = -1 _._ 736, _SE_ = 0.527, _p_ = 0.0055). For clarity, the Idiographic probe outperformed the Descriptive probe ( __<sup></sup> = -1 _._ 7753, _SE_ = 0.558, _p_ = 0.0080), the Explanatory probe ( __<sup></sup> = -1 _._ 9142, _SE_ = 0.559, _p_ = 0.0035), and the Clarifying probe ( __<sup></sup> = -2 _._ 291, _SE_ = 0.651, _p_ = 0.0025). 

**Table 6: Quality measures for the three stages of interviews.** 

|**Stage**|**Probe**|**Informativeness**|**Relevance**|**Specificity**|**Clarity**|
|---|---|---|---|---|---|
|**Exploration**|**Descriptive**|240 (_SD_=233)|1.28 (_SD_=0_._66)|1.25 (_SD_=0_._67)|1.37 (_SD_=0_._55)|
||**Idiographic**|298 (_SD_=244)|1.07 (_SD_=0_._69)|1.18 (_SD_=0_._76)|1.13 (_SD_=0_._60)|
||**Clarifying**|194 (_SD_=173)|0.92 (_SD_=0_._67)|0.82 (_SD_=0_._71)|1.08 (_SD_=0_._53)|
||**Explanatory**|189(_SD_=221)|1.37(_SD_=0_._61)|1.30(_SD_=0_._64)|1.22(_SD_=0_._49)|
|**Requirements**|**Descriptive**|193 (_SD_=154)|1.10 (_SD_=0_._57)|0.91 (_SD_=0_._68)|1.23 (_SD_=0_._51)|
||**Idiographic**|208 (_SD_=196)|1.26 (_SD_=0_._62)|0.90 (_SD_=0_._70)|1.37 (_SD_=0_._49)|
||**Clarifying**|165 (_SD_=141)|0.94 (_SD_=0_._58)|0.71 (_SD_=0_._68)|0.99 (_SD_=0_._42)|
||**Explanatory**|255(_SD_=197)|1.55(_SD_=0_._61)|1.19(_SD_=0_._58)|1.64(_SD_=0_._51)|
|**Evaluation**|**Descriptive**|157 (_SD_=126)|1.02 (_SD_=0_._68)|0.86 (_SD_=0_._66)|1.27 (_SD_=0_._45)|
||**Idiographic**|179 (_SD_=146)|1.28 (_SD_=0_._66)|0.87 (_SD_=0_._69)|1.26 (_SD_=0_._44)|
||**Clarifying**|147 (_SD_=97_._3)|1.14 (_SD_=0_._51)|0.77 (_SD_=0_._66)|1.11 (_SD_=0_._36)|
||**Explanatory**|272 (_SD_=265)|1.55 (_SD_=0_._63)|1.30 (_SD_=0_._70)|1.64 (_SD_=0_._49)|



CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Chatbots for Data Collection in Surveys 

## **5.2 Assessing Participant Perceptions and Experience** 

_Participant Perceptions of the Chatbot._ We found significant differences between the probes in participants' perceptions of the chatbot's repetitiveness (F(60) = 2.922, _p_ = 0.041). Post hoc pairwise comparisons with Bonferroni correction showed significantly higher values for the Explanatory probe ( _M_ = 6.312, _SD_ = 0.957) compared to the Clarifying probe ( _M_ = 4.625, _SD_ = 1.628), (t(24.268) = 3.177, _p_ = 0.039, _d_ = 1.123). We found no difference between the two remaining probes, Descriptive ( _M_ = 5.313, _SD_ = 2.056) or Idiographic ( _M_ = 5.813, _SD_ = 1.109). We found no significant differences between perceived helpfulness (F(60) = 0.733, _p_ = 0.536), usefulness (F(60) = 0.600, _p_ = 0.617), or intrusiveness (F(60) = 1.473, _p_ = 0.231). 

_Smoothness._ We calculated the smoothness score (see Appendix A.3) from the SEQ responses and compared these scores across interview probes. ART showed no significant differences (F(60) = 0.211, _p_ = 0.888) between the Descriptive ( _M_ = 5.288, _SD_ = 1.592), Idiographic ( _M_ = 5.263, _SD_ = 1.047), Clarifying ( _M_ = 5.025, _SD_ = 1.578), and Explanatory ( _M_ = 4.913, _SD_ = 1.427) probes. 

_Perceived Accuracy._ We compared the participants' scoring of their perceived ability to be accurate about their opinions and feelings within each condition. The ART analysis showed no significant differences (F(60) = 1.914, _p_ = 0.137) between the Descriptive ( _M_ = 6.438, _SD_ = 0.727), Idiographic (M = 6.750, _SD_ = 0.447), Clarifying ( _M_ = 6.250, _SD_ = 0.931), and Explanatory ( _M_ = 5.938, _SD_ = 1.482) interview probes. 

## **5.3 Qualitative Insights** 

We now provide qualitative insights into the user experiences and perceptions of the chatbot, as well as their perceptions of utilising chatbots as part of surveys. We did not observe a particular pattern between the different probes, which means we will provide the insights on an aggregated basis. 

_Experiences and Perceptions of Questioning Style._ The open-ended questions regarding experiences and perception of the chatbot's questioning style can be grouped into the ability of the chatbot to facilitate the conversation and disclosure, and the repetitiveness of the probing questions. 

A total of 33 of the participants directly described how the conversational format and the influence of the follow-up questions facilitated them in providing answers to the survey. Participants characterised the chatbot's line of questioning as allowing them to engage in _"deeper"_ (P3, P25, P36) discussions, _"reflect"_ (P3, P19) more before giving an answer, aided in _"narrowing"_ (P59) down their thoughts, providing _"relevant"_ (P15, P24, P25, P28, P47, P53, P55) questions, kept the conversation _"focused"_ (P45) and on _"topic"_ (P28, P39), and generally _"helpful"_ (P2, P17, P38) in helping the participants to express themselves. For instance, participant 57 stated that: _"I do feel that the prompt made me go into more detail than I normally would have gone into. I felt like the questions were open-ended and not leading me in any way"_ , indicating that chatbots in surveys may increase the depth of participant responses to researchers' open-ended questions. As illustrated by participant 2: _'The chatbot's questions were helpful in directing my thoughts towards how I felt about experiences, and connecting those feelings with events. The_ 

_questions were friendly and curious, and actually made me feel seen, and thus more willing to share my thoughts."_ . Other participants stated how they felt better able to; _"elaborate"_ (P24, P27) on their thoughts and feelings, better capable of providing _"detailed"_ (P18, P38, P43, P57, P58) as well as _"meaningful"_ (P3) responses, and that their answering was more _"thorough"_ (P35, P43, P56) than usual. Exemplified by participant 35: _"The chatbot definitely made me much more thorough than I normally would have been with my answers but making sure it understood exactly what I was trying to get across"_ . 

From the open-ended questions, we observed that 15 participants noted how the chatbot, through longer use, exhibited repetitiveness in its line of questioning. For instance, participant 49 stated that: _"The chatbot asked me questions that seemed a bit repetitive at times. The questions were interesting for a couple of times and then it seemed it asked the same line of questioning after that"_ . Highlighting how the lack of an endpoint may lead to experienced repetitiveness of the chatbots' responses. 

_Chatbots as part of Surveys._ We asked participants both about their opinions on using chatbots as part of surveys in regards to the conventional method of open-ended questions as well as considerations on which topics they would disclose to chatbots and humans. 

Of the 64 participants, 38 would prefer to interact with a chatbot compared to filling out open-ended questions in a survey, ten participants preferred to fill out open-ended questions, and 16 either liked both equally or did not care at all. As stated by participant 2: _"Interacting with the chatbot was better than a traditional open-ended survey. Answering questions is easier, more focused, and more natural than just having to come up with a response. The expectations were clear and the bot adapted well to my style of conversing, so I felt motivated to answer thoroughly and honestly"_ . Of the ten participants arguing for open-ended questions, they mentioned the extended time used (P4, P26, P39, P58), that open-ended questions allow the participants themselves to frame the answers to the question (P1, P20, P59), and finally, that it can be difficult to know when to stop the conversation (P46, P59). As illustrated by participant 59 _"They have the benefit of letting me frame my answer the way that I think will communicate my thoughts best. The chatbot does help focus the information, but it can really limit feedback, especially when asking about situations that don't apply."_ . 

When asked if there are any topics they would rather disclose to a chatbot rather than a human in a survey, 14 participants found it easier to disclose to the chatbot, six prefer another human, and 44 did not believe that there are great differences in what they would disclose to a chatbot compared to a human. Of the people preferring a chatbot, they emphasise the strength of the chatbot in that it does not _judge_ their responses when discussing personal topics (P3, P14, P16, P27, P39, P52), for instance, an embarrassing medical question (P27, P39, P44) and on relationships (P2, P38). As exemplified by participant 3: _"I would prefer to disclose more personal or sensitive topics to a chatbot rather than a human because it feels less judgmental and more private, allowing me to express myself freely without the fear of being evaluated"_ . Of the six people preferring humans for disclosing, people refer to the lack of empathy within chatbots and the fear of their personal information becoming a part of the chatbot's data. As participant 20 explains regarding empathy: _"No, there are not any topics I would disclose to a chatbot than to a_ 

CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Jacobsen et al. 

_human. I already know in advance the chatbot cannot feel empathy like a human so I would rather talk to a human, especially if it is a serious topic/discussion on something like mental health"_ . For some, knowing that data typed into a chatbot may persist and not be subject to human forgetfulness may impact the information they are willing to disclose: _"No, I don't want anything I say to get in its algorithm. Especially if it asks for personal or invasive information. A human might eventually forget what I say, but a chatbot will never forget"_ (P32). 

## **5.4 Exploratory Conversational Insights** 

In addition to our findings, we present five exploratory insights derived from participants' conversations with the chatbot. To enhance our previous results, we include selected excerpts from these interactions. These excerpts highlight notable conversational dynamics between participants and the chatbot, offering concrete examples of the subtler positive aspects of using chatbots in surveys. 

_Participants Demanding More Specific Questions._ A key motivation for using chatbots in surveys is their potential to provide clarification when participants find questions unclear. Although this was not a dominant behaviour in our data, we did observe instances where participants directly engaged the chatbot to refine or specify questions they found too vague. In the example conversation (see Appendix A.4.1), the participant perceives the initial question as too broad and requests further clarification through several steps. Eventually, the chatbot is able to narrow down the question to one the participant feels comfortable answering. This interaction highlights how the chatbot's conversational format can adapt to maintain relevance for both the study's objectives and the participant's needs. 

_Clarifying Technology Features as Part of the Evaluation Stage._ During the Evaluation stage of our study, we observed that participants, in addition to assessing the technology, would also ask the chatbot questions about its features. This helped them better understand how those features might impact their daily lives. In the example (see Appendix A.4.2), a participant inquired about the behaviour of calls when using the "Do Not Disturb" feature. After the chatbot's clarification, the participant was able to relate the explanation to their own experiences. 

_Returning to Past Points._ In several instances, participants mentioned multiple technology-related stressors in a single response. The chatbot was able to address these concerns individually, ultimately gaining deeper insights into those issues. In our example (see Appendix A.4.3), the participant expresses concerns about the importance of human presence and the potential overuse of AI in service roles. The chatbot first addresses the topic of human presence before transitioning to the AI concern, ensuring the participant has the opportunity to elaborate on both points. 

_Creating In-Conversation Realisations._ As a result of the conversational format of the survey, we observed participants making subtle realisations about their previous responses during the course of the interaction. In our example (see Appendix A.4.4), one participant initially states that they use technology as an escape, but after several exchanges, returns to that statement, noting "ironically" how difficult it is to actually escape technology. This highlights a key 

advantage of conversational surveys over traditional open-ended questions, which may only capture immediate reactions. In contrast, the chatbot facilitates deeper reflection, enabling participants to refine or reconsider their responses as the conversation progresses. 

_Inquiring through Hypothetical Examples._ As researchers, we are particularly interested in our participants' personal opinions. However, participants may sometimes feel they have nothing relevant to contribute in certain areas of the study. In such cases, we observed that the chatbot was able to reframe questions, encouraging participants to consider how others might experience relief from technological stress. In the example (see Appendix A.4.5), the chatbot and participant engage in a discussion of hypothetical scenarios aimed at gathering suggestions for improving current technologies, such as MS Office Excel. In contrast, a traditional open-ended question might have allowed the participant to move forward without offering any valuable insights. 

## **6 Discussion** 

We investigated the effects of distinct and theory-based interview probes in chatbots for online HCI surveys on response quality and user perceptions. Using a custom chatbot, we explored four interview probes across three stages of HCI research. Our results show that the Idiographic probe performed the best overall in terms of response quality, while the Idiographic, Descriptive, and Clarifying probes performed well across different stages, with the Idiographic consistently leading. Participants rated their chatbot experience similarly across probes, though the Explanatory probe was perceived as more repetitive. Qualitative findings revealed that the chatbot's questioning style effectively encouraged reflection, potentially surpassing traditional open-ended questions. Participants preferred the conversational chatbot for qualitative insights and felt comfortable sharing information with both chatbots and humans, with chatbots favoured for personal thoughts due to their non-judgmental nature. Additionally, our exploratory insights highlighted notable conversational patterns facilitated by chatbots in online surveys. Next, we discuss the use of probes for qualitative data collection in HCI surveys, offering concrete recommendations for the use of specific probes at distinct research stages. We also address the challenges and opportunities for chatbots in online surveys and conclude with limitations and future directions. 

## **6.1 Interview Probes in HCI Surveys** 

Interview probes are a well-established practice of qualitative research across various disciplines. Probes have even been used in a lightweight manner in surveys, where prior responses are embedded into subsequent items [6, 86]. However, there has been limited exploration of how different questioning styles in chatbots influence data collection. Xiao et al. [126] demonstrated that _active listening_ techniques improved engagement and response quality. Building on this, we expand the range of strategies researchers may apply when using chatbots in surveys, drawing from the extensive literature on interview probes [97]. Our approach aims to further enhance participant engagement [51, 65] and improve response quality in chatbot-driven surveys [40, 49, 63, 64, 128, 131]. We found that participants were eager to engage with our chatbot and share their thoughts, opinions, and experiences. Consistent 

CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Chatbots for Data Collection in Surveys 

with previous research [9, 103], we found that the conversational format not only enhanced engagement but also allowed participants to ask clarifying questions, narrow down broad topics, revisit previous points, and explore hypothetical scenarios. This interaction led participants to share more detailed and genuine [71] information, including personal or sensitive insights, with the chatbot [22, 109]. Below we provide recommendations on which interview probes to use within the specific stages of HCI research, and summarised in Table 7. 

_Exploration Stage._ The exploratory stage focuses on understanding users' experiences, needs, and preferences with current or future technologies [69]. Our results show that the Descriptive and Idiographic probes were most effective for gathering rich, usercentred information at this stage. The Descriptive probe encourages participants to share both their actions and thoughts. The probe performed well in relevance and specificity, suggesting that it is effective in capturing narratives that are both relevant to the interview's goals and detailed enough to provide actionable insights. By helping users express both the emotional and situational aspects of their experiences, the Descriptive probe is well-suited for gathering the rich narratives needed in this stage [41, 88]. The Idiographic probe focuses on eliciting specific, detailed memories. It showed strong performance in relevance, specificity and clarity, indicating that it may outperform other probes in eliciting useful information. By aiding participants in shifting from general to vivid recollections [99, 111], the Idiographic probe provides the depth needed to explore user behaviours and challenges, making it a valuable tool in this stage. 

_Requirements Stage._ In the requirements stage, where the goal is to gather detailed insights into users' needs and frustrations with current technologies [69], the Idiographic and Descriptive probes were found to be the most effective in eliciting relevant and specific information. The Idiographic probe, grounded in techniques that encourage users to recall specific, vivid experiences [11, 99, 111], consistently performed well across informativeness, relevance, specificity, and clarity. This suggests that the Idiographic probe is particularly effective at prompting users to provide detailed examples of their needs and challenges, which are essential for defining actionable requirements. By guiding participants to move from 

**Table 7: Overview of high-performing measures for each probe across the three interview stages.** 

||**Exploration**|**Requirements **|**Evaluation**|
|---|---|---|---|
|**Descriptive**|Relevance,<br>Specificity|Relevance,<br>Specificity,<br>Clarity|---|
|**Idiographic**|Relevance,<br>Specificity|Informativeness,<br>Relevance,<br>Specificity,<br>Clarity|Informativeness,<br>Relevance,<br>Specificity,<br>Clarity|
|**Clarifying**|Specificity|Relevance,<br>Clarity|---|
|**Explanatory**|---|---|---|



general recollections to specific memories, the Idiographic probe is well-suited to capture the depth of information necessary for understanding the intricacies of users' experiences. The Descriptive probe, which encourages participants to recount both the emotional and contextual aspects of their experiences [13, 41, 88], also demonstrated strong performance, particularly in relevance, specificity and clarity. This probe appears to be well-suited for gathering broad narratives that encompass both what users do and how they feel about their experiences. In the context of requirements gathering, the Descriptive probe helps to capture not only the specific tasks or challenges users encounter but also the surrounding circumstances and motivations that inform their needs. 

_Evaluation Stage._ In the evaluation stage, where the primary goal is to gather feedback on prototypes or completed products to refine design and functionality [69], the Idiographic probe provided the most valuable insights. The Idiographic probe demonstrated strong performance across informativeness, relevance, specificity, and clarity. By encouraging participants to recall specific, detailed memories [11, 99], the Idiographic probe is well-suited for uncovering nuanced feedback on user experiences with prototypes or products. This detailed recall may help highlight specific aspects of the product that need improvement or clarification, making the Idiographic probe a valuable tool during this stage. 

## **6.2 Challenges and Opportunities for Chatbots in Surveys** 

Our work builds on and extends prior studies that have shown chatbots as a viable solution to collect qualitative data [40, 49, 63, 64, 128, 131]. Nevertheless, we also identified some challenges and new opportunities that warrant further investigation. 

_Integrating Multiple Probes in Conversations._ Our research has demonstrated how different interview probes can yield varying quality results, as dependent on the specific research stage. Our findings are based on brief interactions, due to the survey format, where the chatbot and participant exchange several messages within a short time frame. A valuable avenue for future research is the integration of multiple interview probes within a single conversation, designed to span a longer time frame and engage more deeply with a topic [97]. _I.e._ , the Descriptive probe could be employed to establish an initial topic for discussion, with the Clarifying probe asking for clarifications, and subsequently, the Explanatory probe supporting the participant in identifying relationships between their experiences and opinions. 

_Relinquishing Control in Surveys._ Deploying chatbots in surveys inherently results in reduced control over the study. LLM-based chatbots may behave unpredictably or deviate from the researcher's intended line of questioning. Traditional surveys provide a structured, fixed path for large-scale data collection, but managing the dynamic nature of chatbot-driven interactions can pose challenges [37, 52, 98]. However, this conversational format also presents an opportunity to gather richer qualitative data than enabled by traditional surveys. The use of theory-based interview probes, as explored in this paper, offers a way to maintain control while still fostering an engaging and flexible survey experience for participants [113]. 

CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Jacobsen et al. 

_Wrapping up Conversations or Topics._ The chatbot in our study did not enforce a specific endpoint for the conversation. Instead, participants were instructed to type 'goodbye' when they wished to move on. Despite the fact that participants controlled the start and end of the conversation, several participants felt the questions became repetitive, addressing points they had already covered. While clearer instructions could potentially mitigate this issue, we envision future opportunities to computationally assess conversations in real time, allowing the chatbot to suggest when it is appropriate to progress, rather than relying on participants to end the interaction. This highlights an important balance between achieving the desired conversational depth and avoiding participant fatigue [68, 89--91]. 

This is not without challenges, as assessing whether a participant has provided the extent of detail they are able and willing to share, or whether further probing might uncover additional insights is inherently difficult---including in human-driven interviews. To address this, we propose three distinct opportunities for researchers to explore. First, one potential direction is to determine the conclusion of a chatbot conversation by evaluating whether participant responses meet predefined quality criteria. For instance, an additional agent could evaluate each response to determine whether it sufficiently addresses the chatbot's questions. Second, a more complex solution involves conducting a computational analysis of the entire conversation. This approach aligns with the broader challenge of addressing data saturation [38, 81] (or data adequacy) within qualitative research. While computational methods may offer the capability to predict a level of saturation and guide the conversation to a conclusion, this foundational challenge may be out of scope to resolve in an automated fashion. Third, we propose that an agent could evaluate a decreasing trend in the quality of participant responses. For example, this could involve analysing responses for signs of repetitiveness, reduced answer length, or a diminishing level of detail, which might indicate a decline in engagement or cognitive fatigue [60]. These suggestions are, of course, non-exhaustive, but offer potential trajectories for dynamically determining the termination of chatbot conversations in surveys. 

_Contextuality is Conserved in the Conversation._ A key observation from our study is the nuanced richness provided by the chat data. Similar to face-to-face interviews, the most valuable insights often lie not in individual participant statements but in the broader context of the conversation. We regularly observed that participants struggled to articulate their thoughts early on in the chat, but that the step-by-step probing gradually elicited deeper insights, sometimes even to the surprise of the participants themselves. These reflections, which may have been lost without probing, underscore the potential for chatbots in the context of surveys. However, for effective conversational data, the participant's initial responses must provide sufficient detail to enable the chatbot to generate meaningful follow-up probing questions [25, 79]. Without this foundation, the quality of the probing and the depth of insights may be limited, highlighting the importance of designing chatbot interactions that encourage detailed initial participant responses. 

## **6.3 Limitations and Future Work** 

We acknowledge several limitations in our study. In this study, we investigated the utilisation of theory-based interview probes for 

qualitative data collection in surveys through chatbots, however, comparing the effectiveness of surveys with LLM-based chatbots with traditional open-ended questions fell outside of our scope. Future research could investigate the quality of responses generated by LLM-based chatbots as compared to traditional open-ended survey questions to better understand their relative strengths and limitations, further extending the work of Xiao et al. [128]. This line of investigation could include both qualitative and quantitative approaches. For instance, manual thematic analysis could be employed to uncover patterns in the data, such as the depth and richness of the responses, the coherence of narratives, or the relevance of ideas to the questions posed. Computational analyses, on the other hand, could provide complementary insights by systematically evaluating various quality dimensions, such as response diversity, originality, sentiment, and informativeness, as exemplified by metrics like the diversity of ideas [23]. Furthermore, comparisons could be expanded to evaluate how specific enhancements, such as interview probes, influence the quality of data when used in conjunction with state-of-the-art LLMs. For example, these comparisons could examine whether probes elicit more detailed, contextually relevant, or actionable responses compared to pre-defined chatbot interactions. Studies might also investigate how participants perceive the clarity and supportiveness of probe-augmented chatbots versus traditional approaches or simpler LLM-driven systems without additional instructions. By addressing these questions, future research could not only assess the added value of interview probes but also offer practical recommendations for designing chatbots tailored to specific research goals. This would help advance the use of LLM-based tools in domains requiring high-quality qualitative data collection. 

Second, we chose to focus on the phenomenon of technologically induced stress as the survey's topic, which provided a useful context for examining the interview probes. However, we recognise that this topic may not be representative of broader areas in HCI research. For instance, in the exploratory stage, researchers may not yet have a well-defined research problem, making depth-seeking interview probes less applicable. Additionally, while chatbots may be advantageous for evaluating specific design features in online surveys, the use of interview probes in this context may not generate the intended insights for guiding future design directions. Future work could, therefore, investigate the use of interview probes in different areas of HCI. 

Third, we observed that the evaluation stage both elicited fewer responses and resulted in lower scores on the quality measures. We believe this may be due to two factors. One possibility is participant fatigue, as the evaluation stage occurs at the end of the process, potentially leading to diminished engagement. Alternatively, the lower response quality may reflect the inherent limitations in the insights participants can offer during the evaluation stage. Regardless, it is essential for future research to further investigate the dynamics of the evaluation stage, particularly in the context of using chatbots in surveys. 

## **7 Conclusion** 

We developed an LLM-based chatbot to investigate the use of theorybased interview probes for collecting qualitative data in online surveys across three stages of HCI research. Specifically, we evaluated Descriptive, Idiographic, Clarifying, and Exploration probes 

CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Chatbots for Data Collection in Surveys 

across the stages of Exploration, Reqirements, and Evaluation. Our results show that the Idiographic and Descriptive probes provide high-quality insights in the Exploration and Reqirements stage, and that the Idiographic probe performs well in the Evaluation stage. We found no larger experiential differences between the different probes, but uncovered several perceptions on the use of chatbots in service including exploratory conversational patterns. We provide concrete recommendations for the use of chatbots with interview probes in online surveys and critically discuss further challenges and opportunities on how to continue research into this promising way for online survey data collection. 

## **Acknowledgments** 

This work is supported by the Carlsberg Foundation, grant CF210159. 

## **References** 

- [1] David Agogo and Traci J. Hess. 2018. "How does tech make you feel?" a review and examination of negative affective responses to technology use. _European Journal of Information Systems_ 27, 5 (2018), 570--599. doi:10.1080/0960085X.2018. 1435230 

- [2] Pengcheng An, Jiawen Stefanie Zhu, Zibo Zhang, Yifei Yin, Qingyuan Ma, Che Yan, Linghao Du, and Jian Zhao. 2024. EmoWear: Exploring Emotional Teasers for Voice Message Interaction on Smartwatches. In _Proceedings of the CHI Conference on Human Factors in Computing Systems_ (Honolulu, HI, USA) _(CHI '24)_ . Association for Computing Machinery, New York, NY, USA, Article 279, 16 pages. doi:10.1145/3613904.3642101 

- [3] Ramakrishna Ayyagari, Varun Grover, and Russell Purvis. 2011. Technostress: Technological Antecedents and Implications. _MIS Quarterly_ 35, 4 (2011), 831-- 858. 

- [4] Christoph Bartneck, Dana Kulic, Elizabeth Croft, and Susana Zoghbi. 2009. Measurement Instruments for the Anthropomorphism, Animacy, Likeability, Perceived Intelligence, and Perceived Safety of Robots. _International Journal of Social Robotics_ 1, 1 (2009), 71--81. doi:10.1007/s12369-008-0001-3 

- [5] Douglas Bates, Martin Machler, Ben Bolker, and Steve Walker. 2015. Fitting Linear Mixed-Effects Models Using lme4. _Journal of Statistical Software_ 67, 1 (2015), 1--48. doi:10.18637/jss.v067.i01 

- [6] Dorothee Behr, Lars Kaczmirek, Wolfgang Bandilla, and Michael Braun. 2012. Asking Probing Questions in Web Surveys: Which Factors have an Impact on the Quality of Responses? _Social Science Computer Review_ 30, 4 (2012), 487--498. doi:10.1177/0894439311435305 

- [7] Samuel Bell, Clara Wood, and Advait Sarkar. 2019. Perceptions of Chatbots in Therapy. In _Extended Abstracts of the 2019 CHI Conference on Human Factors in Computing Systems_ (Glasgow, Scotland Uk) _(CHI EA '19)_ . Association for Computing Machinery, New York, NY, USA, 1--6. doi:10.1145/3290607.3313072 

- [8] Timothy Bickmore and Justine Cassell. 2001. Relational agents: a model and implementation of building user trust. In _Proceedings of the SIGCHI Conference on Human Factors in Computing Systems_ (Seattle, Washington, USA) _(CHI '01)_ . Association for Computing Machinery, New York, NY, USA, 396--403. doi:10. 1145/365024.365304 

- [9] Timothy Bickmore, Laura Pfeifer, and Daniel Schulman. 2011. Relational Agents Improve Engagement and Learning in Science Museum Visitors BT - Intelligent Virtual Agents. In _Intelligent Virtual Agents_ , Hannes Hogni Vilhjalmsson, Stefan Kopp, Stacy Marsella, and Kristinn R Thorisson (Eds.). Springer Berlin Heidelberg, Berlin, Heidelberg, 55--67. 

- [10] Dan Bohus and Alexander I. Rudnicky. 2009. The RavenClaw dialog management framework: Architecture and systems. _Computer Speech & Language_ 23, 3 (2009), 332--361. doi:10.1016/j.csl.2008.10.001 

- [11] William F Brewer. 1986. What is autobiographical memory? In _Autobiographical memory._ Cambridge University Press, New York, NY, US, 25--49. doi:10.1017/ CBO9780511558313.006 

- [12] Svend Brinkman and Steinar Kvale. 2018. Doing Interviews. http://digital. casalini.it/9781526426093http://digital.casalini.it/5017966 

- [13] Jerome Bruner. 1990. _Acts of meaning_ . Vol. 3. Harvard University Press, Cambridge, MA, USA. 

- [14] Elina Ruuskanen Camilla Priede, Anniina Jokinen and Stephen Farrall. 2014. Which probes are most useful when undertaking cognitive interviews? _International Journal of Social Research Methodology_ 17, 5 (2014), 559--568. doi:10.1080/ 13645579.2013.799795 

- [15] Marta E. Cecchinato and Anna L. Cox. 2020. Boundary management and communication technologies. In _The Oxford Handbook of Digital Technology and Society_ . Oxford University Press, -, 299--320. doi:10.1093/oxfordhb/9780190932596.013.10 

- [16] Irene Celino and Gloria Re Calegari. 2020. Submitting surveys via a conversational interface: An evaluation of user acceptance and approach effectiveness. _International Journal of Human-Computer Studies_ 139 (2020), 102410. https://doi.org/10.1016/j.ijhcs.2020.102410 

- [17] Qinyue Chen, Yuchun Yan, and Hyeon-Jeong Suk. 2021. Bubble Coloring to Visualize the Speech Emotion. In _Extended Abstracts of the 2021 CHI Conference on Human Factors in Computing Systems_ (Yokohama, Japan) _(CHI EA '21)_ . Association for Computing Machinery, New York, NY, USA, Article 361, 6 pages. doi:10.1145/3411763.3451698 

- [18] Yukina Chen. 2017. _The Effects of Question Customization on the Quality of an Open-Ended Question_ . Nebraska Department of Education, Nebraska, USA. 

- [19] Martin A. Conway. 2005. Memory and the self. _Journal of Memory and Language_ 53, 4 (2005), 594--628. doi:10.1016/j.jml.2005.08.005 

- [20] Bernardo Cortes, Julia Teles, and Emilia Duarte. 2023. Exploring Emotions in Avatar Design to Increase Adherence to Chatbot Technology. In _Design, User Experience, and Usability_ , Aaron Marcus, Elizabeth Rosenzweig, and Marcelo M. Soares (Eds.). Springer Nature Switzerland, Cham, 273--282. 

- [21] Mick P Couper. 2008. _Designing effective Web surveys._ Cambridge University Press, New York, NY, US. xvii, 398--xvii, 398 pages. doi:10.1017/ CBO9780511499371 

- [22] Samuel Rhys Cox and Wei Tsang Ooi. 2022. Does Chatbot Language Formality Affect Users' Self-Disclosure?. In _Proceedings of the 4th Conference on Conversational User Interfaces_ (Glasgow, United Kingdom) _(CUI '22)_ . Association for Computing Machinery, New York, NY, USA, Article 1, 13 pages. doi:10.1145/3543829.3543831 

- [23] Samuel Rhys Cox, Yunlong Wang, Ashraf Abdul, Christian von der Weth, and Brian Y. Lim. 2021. Directed Diversity: Leveraging Language Embedding Distances for Collective Creativity in Crowd Ideation. In _Proceedings of the 2021 CHI Conference on Human Factors in Computing Systems_ (Yokohama, Japan) _(CHI '21)_ . Association for Computing Machinery, New York, NY, USA, Article 393, 35 pages. doi:10.1145/3411764.3445782 

- [24] Justin Cranshaw, Emad Elwany, Todd Newman, Rafal Kocielnik, Bowen Yu, Sandeep Soni, Jaime Teevan, and Andres Monroy-Hernandez. 2017. Calendar.help: Designing a Workflow-Based Scheduling Agent with Humans in the Loop. In _Proceedings of the 2017 CHI Conference on Human Factors in Computing Systems_ (Denver, Colorado, USA) _(CHI '17)_ . Association for Computing Machinery, New York, NY, USA, 2382--2393. doi:10.1145/3025453.3025780 

- [25] Sumit Kumar Dam, Choong Seon Hong, Yu Qiao, and Chaoning Zhang. 2024. A Complete Survey on LLM-based AI Chatbots. arXiv:2406.16937 [cs.CL] https: //arxiv.org/abs/2406.16937 

- [26] David DeVault, Ron Artstein, Grace Benn, Teresa Dey, Ed Fast, Alesia Gainer, Kallirroi Georgila, Jon Gratch, Arno Hartholt, Margaux Lhommet, Gale Lucas, Stacy Marsella, Fabrizio Morbini, Angela Nazarian, Stefan Scherer, Giota Stratou, Apar Suri, David Traum, Rachel Wood, Yuyu Xu, Albert Rizzo, and Louis-Philippe Morency. 2014. SimSensei kiosk: a virtual human interviewer for healthcare decision support. In _Proceedings of the 2014 International Conference on Autonomous Agents and Multi-Agent Systems_ (Paris, France) _(AAMAS '14)_ . International Foundation for Autonomous Agents and Multiagent Systems, Richland, SC, 1061--1068. 

- [27] Nico Dragano and Thorsten Lunau. 2020. Technostress at work and mental health: concepts and research results, In Current opinion in psychiatry. _Current Opinion in Psychiatry_ 33, 4, 407--413. 

- [28] Laila Dybkjr, Niels Ole Bernsen, and Hans Dybkjr. 1996. Grice incorporated: cooperativity in spoken dialogue. In _Proceedings of the 16th Conference on Computational Linguistics - Volume 1_ (Copenhagen, Denmark) _(COLING '96)_ . Association for Computational Linguistics, USA, 328--333. doi:10.3115/992628.992686 

- [29] Laila Dybkjr, Niels Ole Bernsen, and Wolfgang Minker. 2004. Evaluation and usability of multimodal spoken language dialogue systems. _Speech Communication_ 43, 1 (2004), 33--54. doi:10.1016/j.specom.2004.02.001 

- [30] Joel R Evans and Anil Mathur. 2005. The value of online surveys. _Internet Research_ 15, 2 (jan 2005), 195--219. doi:10.1108/10662240510590360 

- [31] Joel R Evans and Anil Mathur. 2018. The value of online surveys: a look back and a look ahead. _Internet Research_ 28, 4 (2018), 854--887. doi:10.1108/IntR-032018-0089 

- [32] Franz Faul, Edgar Erdfelder, Axel Buchner, and Albert-Georg Lang. 2009. Statistical power analyses using G*Power 3.1: Tests for correlation and regression analyses. _Behavior Research Methods_ 41, 4 (2009), 1149--1160. doi:10.3758/BRM. 41.4.1149 

- [33] Rowanne Fleck, Anna L. Cox, and Rosalyn A.V. Robison. 2015. Balancing Boundaries: Using Multiple Devices to Manage Work-Life Balance. In _Proceedings of the 33rd Annual ACM Conference on Human Factors in Computing Systems_ (Seoul, Republic of Korea) _(CHI '15)_ . Association for Computing Machinery, New York, NY, USA, 3985--3988. doi:10.1145/2702123.2702386 

- [34] Asbjrn Flstad and Petter Bae Brandtzg. 2017. Chatbots and the new world of HCI. _Interactions_ 24, 4 (jun 2017), 38--42. doi:10.1145/3085558 

- [35] Eric N. Forsythand and Craig H. Martell. 2007. Lexical and Discourse Analysis of Online Chat Dialog. In _International Conference on Semantic Computing (ICSC 2007)_ . IEEE, Irvine, CA, USA, 19--26. doi:10.1109/ICSC.2007.55 

CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Jacobsen et al. 

- [36] Anne Fota, Katja Wagner, Tobias Roeding, and Hanna Schramm-Klein. 2022. "Help! I Have a Problem" -- Differences between a Humanlike and Robot-like Chatbot Avatar in Complaint Management. In _Proceedings of the 55th Hawaii International Conference on System Sciences (HICSS-55)_ (Online, 3-7). AIS Electronic Library (AISeL), Hawaii, USA, 4273--4282. https://aisel.aisnet.org/hicss55/in/avatars/3/ 

- [37] Scott Fricker, Mirta Galesic, Roger Tourangeau, and Ting Yan. 2005. An Experimental Comparison of Web and Telephone Surveys. _Public Opinion Quarterly_ 69, 3 (01 2005), 370--392. doi:10.1093/poq/nfi027 

- [38] Patricia I Fusch and Lawrence R Ness. 2015. Are we there yet? Data saturation in qualitative research. _The Qualitative Report_ 20 (nov 2015), 1408+. 

- [39] Ujwal Gadiraju, Ricardo Kawase, Stefan Dietze, and Gianluca Demartini. 2015. Understanding Malicious Behavior in Crowdsourcing Platforms: The Case of Online Surveys. In _Proceedings of the 33rd Annual ACM Conference on Human Factors in Computing Systems_ (Seoul, Republic of Korea) _(CHI '15)_ . Association for Computing Machinery, New York, NY, USA, 1631--1640. doi:10.1145/2702123. 2702443 

- [40] Yubin Ge, Ziang Xiao, Jana Diesner, Heng Ji, Karrie Karahalios, and Hari Sundaram. 2023. What should I Ask: A Knowledge-driven Approach for Follow-up Questions Generation in Conversational Surveys. arXiv:2205.10977 

- [41] R.L. Gorden. 1987. _Interviewing: Strategy, Techniques, and Tactics_ . Dorsey Press, California, USA. 

- [42] A.C. Graesser, P. Chipman, B.C. Haynes, and A. Olney. 2005. AutoTutor: an intelligent tutoring system with mixed-initiative dialogue. _IEEE Transactions on Education_ 48, 4 (2005), 612--618. doi:10.1109/TE.2005.856149 

- [43] H.P. Grice. 1989. _Studies in the Way of Words_ . Harvard University Press. 

- [44] Paul Grice. 1975. Logic and Conversation. _Syntax and Semantics 3: Speech Acts_ (1975), 41--58. 

- [45] Carla F. Griggio, Arissa J. Sato, Wendy E. Mackay, and Koji Yatani. 2021. Mediating Intimacy with DearBoard: a Co-Customizable Keyboard for Everyday Messaging. In _Proceedings of the 2021 CHI Conference on Human Factors in Computing Systems_ (Yokohama, Japan) _(CHI '21)_ . Association for Computing Machinery, New York, NY, USA, Article 342, 16 pages. doi:10.1145/3411764.3445757 

- [46] Jonathan Grudin and Richard Jacques. 2019. Chatbots, Humbots, and the Quest for Artificial General Intelligence. In _Proceedings of the 2019 CHI Conference on Human Factors in Computing Systems_ (Glasgow, Scotland Uk) _(CHI '19)_ . Association for Computing Machinery, New York, NY, USA, 1--11. doi:10.1145/ 3290605.3300439 

- [47] Jonathan Grudin, Shari Tallarico, and Scott Counts. 2005. As technophobia disappears: implications for design. In _Proceedings of the 2005 ACM International Conference on Supporting Group Work_ (Sanibel Island, Florida, USA) _(GROUP '05)_ . Association for Computing Machinery, New York, NY, USA, 256--259. doi:10. 1145/1099203.1099247 

- [48] Joseph F Hair, William C Black, Barry J Babin, Rolph E Anderson, and RL Tatham. 2010. _Multivariate Data Analysis_ . Pearson, Kennesaw State University. 

- [49] Christopher Harms and Sebastian Schmidt. 2017. Conversational Survey Frontends: How Can Chatbots Improve Online Surveys? 

- [50] Mariam Hassib, Daniel Buschek, Pawe W. Wozniak, and Florian Alt. 2017. HeartChat: Heart Rate Augmented Mobile Chat to Support Empathy and Awareness. In _Proceedings of the 2017 CHI Conference on Human Factors in Computing Systems_ (Denver, Colorado, USA) _(CHI '17)_ . Association for Computing Machinery, New York, NY, USA, 2239--2251. doi:10.1145/3025453.3025758 

- [51] Dirk Heerwegh and Geert Loosveldt. 2007. Personalizing E-mail Contacts: Its Influence on Web Survey Response Rate and Social Desirability Response Bias. _International Journal of Public Opinion Research_ 19, 2 (jul 2007), 258--268. doi:10.1093/ijpor/edl028 

- [52] Dirk Heerwegh and Geert Loosveldt. 2008. Face-to-Face versus Web Surveying in a High-Internet-Coverage Population: Differences in Response Quality. _Public Opinion Quarterly_ 72, 5 (10 2008), 836--846. doi:10.1093/poq/nfn045 

- [53] Charles T. Hemphill, John J. Godfrey, and George R. Doddington. 1990. The ATIS spoken language systems pilot corpus. In _Proceedings of the Workshop on Speech and Natural Language_ (Hidden Valley, Pennsylvania) _(HLT '90)_ . Association for Computational Linguistics, USA, 96--101. doi:10.3115/116580.116613 

- [54] K. Hofland and S. Johansson. 1982. _Word Frequencies in British and American English_ . Norwegian Computing Centre for the Humanities. 

- [55] Kate S. Hone and Robert Graham. 2000. Towards a tool for the Subjective Assessment of Speech System Interfaces (SASSI). _Natural Language Engineering_ 6, 3--4 (2000), 287--303. doi:10.1017/S1351324900002497 

- [56] D.S. Jones. 1979. _Elementary Information Theory_ . Clarendon Press. [57] Sidney M Jourard. 1971. _Self-disclosure: An experimental analysis of the transparent self._ John Wiley, Oxford, England. xiii, 248--xiii, 248 pages. 

- [58] Eunbin Kang and Youn Ah Kang. 2024. Counseling chatbot design: The effect of anthropomorphic chatbot characteristics on user self-disclosure and companionship. _International Journal of Human--Computer Interaction_ 40, 11 (2024), 2781--2795. 

- [59] Jie Kang, Kyle Condiff, Shuo Chang, Joseph A. Konstan, Loren Terveen, and F. Maxwell Harper. 2017. Understanding How People Use Natural Language to Ask for Recommendations. In _Proceedings of the Eleventh ACM Conference_ 

   - _on Recommender Systems_ (Como, Italy) _(RecSys '17)_ . Association for Computing Machinery, New York, NY, USA, 229--237. doi:10.1145/3109859.3109873 

- [60] Enamul Karim, Hamza Reza Pavel, Sama Nikanfar, Aref Hebri, Ayon Roy, Harish Ram Nambiappan, Ashish Jaiswal, Glenn R. Wylie, and Fillia Makedon. 2024. Examining the Landscape of Cognitive Fatigue Detection: A Comprehensive Survey. _Technologies_ 12, 3 (2024). doi:10.3390/technologies12030038 

- [61] Saul Kassin, Steven Fein, and Hazel Rose Markus. 2023. _Social psychology_ . SAGE Publications. 

- [62] Odai Y. Khasawneh. 2018. Technophobia: Examining its hidden factors and defining it. _Technology in Society_ 54 (2018), 93--100. doi:10.1016/j.techsoc.2018. 03.008 

- [63] Soomin Kim, Joonhwan Lee, and Gahgene Gweon. 2019. Comparing Data from Chatbot and Web Surveys: Effects of Platform and Conversational Style on Survey Response Quality. In _Proceedings of the 2019 CHI Conference on Human Factors in Computing Systems_ (Glasgow, Scotland Uk) _(CHI '19)_ . Association for Computing Machinery, New York, NY, USA, 1--12. doi:10.1145/3290605.3300316 

- [64] Rafal Kocielnik, Raina Langevin, James S. George, Shota Akenaga, Amelia Wang, Darwin P. Jones, Alexander Argyle, Callan Fockele, Layla Anderson, Dennis T. Hsieh, Kabir Yadav, Herbert Duber, Gary Hsieh, and Andrea L. Hartzler. 2021. Can I Talk to You about Your Social Needs? Understanding Preference for Conversational User Interface in Health. In _Proceedings of the 3rd Conference on Conversational User Interfaces_ (Bilbao (online), Spain) _(CUI '21)_ . Association for Computing Machinery, New York, NY, USA, Article 4, 10 pages. doi:10.1145/ 3469595.3469599 

- [65] Jon A Krosnick. 1999. Survey Research. _Annual Review of Psychology_ 50, 1 (1999), 537--567. doi:10.1146/annurev.psych.50.1.537 

- [66] John Kupersmith. 1992. Technostress and the reference librarian. _Reference Services Review_ 20, 2 (1992), 7--50. doi:10.1108/eb049150 

- [67] Antonius Angga Kurniawan, W Edwin Fachri, A Elevanita, Suryadi, and R Dewi Agushinta. 2015. Design of chatbot with 3D avatar, voice interface, and facial expression. In _2015 International Conference on Science in Information Technology (ICSITech)_ . 326--330. doi:10.1109/ICSITech.2015.7407826 

- [68] Paul Lavrakas. 2008. Encyclopedia of Survey Research Methods. doi:10.4135/ 9781412963947 

- [69] Jonathan Lazar, Jinjuan Heidi Feng, and Harry Hochheiser. 2017. _Research Methods in Human Computer Interaction_ (2nd edition ed.). Morgan Kaufmann, Cambridge, MA. 

- [70] Geoffrey Leech. 1993. 100 million words of English. _English Today_ 9, 1 (1993), 9--15. doi:10.1017/S0266078400006854 

- [71] Jingyi Li, Michelle X. Zhou, Huahai Yang, and Gloria Mark. 2017. Confiding in and Listening to Virtual Agents: The Effect of Personality. In _Proceedings of the 22nd International Conference on Intelligent User Interfaces_ (Limassol, Cyprus) _(IUI '17)_ . Association for Computing Machinery, New York, NY, USA, 275--286. doi:10.1145/3025171.3025206 

- [72] Q. Vera Liao, Muhammed Mas-ud Hussain, Praveen Chandar, Matthew Davis, Yasaman Khazaeni, Marco Patricio Crasso, Dakuo Wang, Michael Muller, N. Sadat Shami, and Werner Geyer. 2018. All Work and No Play?. In _Proceedings of the 2018 CHI Conference on Human Factors in Computing Systems_ (Montreal QC, Canada) _(CHI '18)_ . Association for Computing Machinery, New York, NY, USA, 1--13. doi:10.1145/3173574.3173577 

- [73] Yuting Liao and Jiangen He. 2020. Racial mirroring effects on human-agent interaction in psychotherapeutic conversations. In _Proceedings of the 25th international conference on intelligent user interfaces_ . 430--442. 

- [74] Stephen W Littlejohn and Karen A Foss. 2010. _Theories of human communication_ . Waveland press. 

- [75] Chia-Wei Liu, Ryan Lowe, Iulian V. Serban, Michael Noseworthy, Laurent Charlin, and Joelle Pineau. 2017. How NOT To Evaluate Your Dialogue System: An Empirical Study of Unsupervised Evaluation Metrics for Dialogue Response Generation. arXiv:1603.08023 [cs.CL] 

- [76] Ewa Luger and Abigail Sellen. 2016. "Like Having a Really Bad PA": The Gulf between User Expectation and Experience of Conversational Agents. In _Proceedings of the 2016 CHI Conference on Human Factors in Computing Systems_ (San Jose, California, USA) _(CHI '16)_ . Association for Computing Machinery, New York, NY, USA, 5286--5297. doi:10.1145/2858036.2858288 

- [77] Gloria Mark, Yiran Wang, and Melissa Niiya. 2014. Stress and multitasking in everyday college life: an empirical study of online activity. In _Proceedings of the SIGCHI Conference on Human Factors in Computing Systems_ (Toronto, Ontario, Canada) _(CHI '14)_ . Association for Computing Machinery, New York, NY, USA, 41--50. doi:10.1145/2556288.2557361 

- [78] Scott McGlashan, Norman Fraser, Nigel Gilbert, Eric Bilange, Paul Heisterkamp, and Nick Youd. 1992. Dialogue management for telephone information systems. In _Proceedings of the Third Conference on Applied Natural Language Processing_ (Trento, Italy) _(ANLC '92)_ . Association for Computational Linguistics, USA, 245--246. doi:10.3115/974499.974549 

- [79] Michael McTear, Sheen Varghese Marokkie, and Yaxin Bi. 2023. A Comparative Study of Chatbot Response Generation: Traditional Approaches Versus Large Language Models. In _Knowledge Science, Engineering and Management_ , Zhi Jin, Yuncheng Jiang, Robert Andrei Buchmann, Yaxin Bi, Ana-Maria Ghiran, and 

CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Chatbots for Data Collection in Surveys 

   - Wenjun Ma (Eds.). Springer Nature Switzerland, Cham, 70--79. 

- [80] Elliot G Mishler. 1991. _Research interviewing: Context and narrative_ . Harvard university press. 

- [81] Janice M Morse. 1995. The Significance of Saturation. _Qualitative Health Research_ 5, 2 (may 1995), 147--149. doi:10.1177/104973239500500201 

- [82] Hendrik Muller and Aaron Sedley. 2015. Designing Surveys for HCI Research. In _Proceedings of the 33rd Annual ACM Conference Extended Abstracts on Human Factors in Computing Systems_ (Seoul, Republic of Korea) _(CHI EA '15)_ . Association for Computing Machinery, New York, NY, USA, 2485--2486. doi:10.1145/2702613. 2706683 

- [83] Venetia Notara, Elissavet Vagka, Charalampos Gnardellis, and Areti Lagiou. 2021. The Emerging Phenomenon of Nomophobia in Young Adults: A Systematic Review Study. _Addiction & health_ 13, 2 (2021), 120--136. doi:10.22122/ahj.v13i2. 309 

- [84] David Novick and Ivan Gris. 2014. Building Rapport between Human and ECA: A Pilot Study. In _Human-Computer Interaction. Advanced Interaction Modalities and Techniques_ , Masaaki Kurosu (Ed.). Springer International Publishing, Cham, 472--480. 

- [85] Kristen Olson, James Wagner, and Raeda Anderson. 2020. Survey Costs: Where are We and What is the Way Forward? _Journal of Survey Statistics and Methodology_ 9, 5 (2020), 921--942. doi:10.1093/jssam/smaa014 

- [86] Marije Oudejans. 2018. Using interactive features to motivate and probe responses to open-ended questions. In _Social and behavioral research and the internet_ . Routledge, 215--244. 

- [87] Tero Parviainen. 2010. Web Text Corpus. https://github.com/teropa/nlp/tree/ master/resources/corpora/webtext. [Accessed 09-05-2024]. 

- [88] Monisha Pasupathi. 2001. The social construction of the personal past and its implications for adult development. 651--672 pages. doi:10.1037/0033-2909.127. 5.651 

- [89] S.R. Porter. 2004. _Overcoming Survey Research Problems: New Directions for Institutional Research_ . Wiley. 

- [90] Stephen R. Porter. 2004. Raising response rates: What works? _New Directions for Institutional Research_ 2004, 121 (2004), 5--21. doi:10.1002/ir.97 

- [91] Stephen R Porter, Michael E Whitcomb, and William H Weitzer. 2004. Multiple surveys of students and survey fatigue. _New Directions for Institutional Research_ 2004, 121 (2004), 63--73. doi:10.1002/ir.101 

- [92] Bob Price. 2002. Laddered questions and qualitative data research interviews. _Journal of Advanced Nursing_ 37, 3 (2002), 273--281. doi:10.1046/j.1365-2648.2002. 02086.x 

- [93] Filip Radlinski and Nick Craswell. 2017. A Theoretical Framework for Conversational Search. In _Proceedings of the 2017 Conference on Conference Human Information Interaction and Retrieval_ (Oslo, Norway) _(CHIIR '17)_ . Association for Computing Machinery, New York, NY, USA, 117--126. doi:10.1145/3020165.3020183 

- [94] Ursa Reja, Katja Lozar Manfreda, Valentina Hlebec, and Vasja Vehovar. 2003. _Open-ended vs. close-ended questions in Web questionnaires_ . 159--177. http: //mrvar.fdv.uni-lj.si/pub/mz/mz19/reja.pdf 

- [95] Francesco Ricci, Lior Rokach, and Bracha Shapira. 2022. Recommender Systems: Techniques, Applications, and Challenges BT - Recommender Systems Handbook. Springer US, New York, NY, 1--35. doi:10.1007/978-1-0716-2197-4_1 

- [96] Rene Riedl. 2012. On the biology of technostress: literature review and research agenda. _SIGMIS Database_ 44, 1 (2012), 18--55. doi:10.1145/2436239.2436242 

- [97] Oliver C. Robinson. 2023. Probing in qualitative research interviews: Theory and practice. _Qualitative Research in Psychology_ 20, 3 (2023), 382--397. doi:10. 1080/14780887.2023.2238625 

- [98] Catherine A. Roster, Robert D. Rogers, Gerald Albaum, and Darin Klein. 2004. A Comparison of Response Characteristics from Web and Telephone Surveys. _International Journal of Market Research_ 46, 3 (2004), 359--373. doi:10.1177/ 147078530404600301 

- [99] Jonathan Rottenberg, Jennifer Hildner, and Ian Gotlib. 2006. Idiographic autobiographical memories in major depressive disorder. _Cognition and Emotion_ 20, 1 (2006), 114--128. doi:10.1080/02699930500286299 

- [100] Kathryn Roulston. 2014. Reflective Interviewing: A Guide to Theory and Practice. doi:10.4135/9781446288009 

- [101] Bernard H Russel. 2013. Social research methods: qualitative and quantitative approaches. 

- [102] Jessica Schroeder, Chelsey Wilkes, Kael Rowan, Arturo Toledo, Ann Paradiso, Mary Czerwinski, Gloria Mark, and Marsha M. Linehan. 2018. Pocket Skills: A Conversational Mobile Web App To Support Dialectical Behavioral Therapy. In _Proceedings of the 2018 CHI Conference on Human Factors in Computing Systems_ (Montreal QC, Canada) _(CHI '18)_ . Association for Computing Machinery, New York, NY, USA, 1--15. doi:10.1145/3173574.3173972 

- [103] Ameneh Shamekhi, Q. Vera Liao, Dakuo Wang, Rachel K. E. Bellamy, and Thomas Erickson. 2018. Face Value? Exploring the Effects of Embodiment for a Group Facilitation Agent. In _Proceedings of the 2018 CHI Conference on Human Factors in Computing Systems_ (Montreal QC, Canada) _(CHI '18)_ . Association for Computing Machinery, New York, NY, USA, 1--13. doi:10.1145/3173574.3173965 

- [104] Eleanor Singer and Mick P. Couper. 2017. Some Methodological Uses of Responses to Open Questions and Other Verbatim Comments in Quantitative 

   - Surveys. _Methods, data, analyses : a journal for quantitative methods and survey methodology (mda)_ 11, 2 (2017), 115--134. doi:10.12758/mda.2017.01 

- [105] Jonathan A Smith and Mike Osborn. 2003. Interpretative phenomenological analysis. In _Qualitative psychology: A practical guide to research methods._ Sage Publications, Inc, Thousand Oaks, CA, US, 51--80. 

- [106] Stephen Wonchul Song and Mincheol Shin. 2024. Uncanny Valley Effects on Chatbot Trust, Purchase Intention, and Adoption Intention in the Context of E-Commerce: The Moderating Role of Avatar Familiarity. _International Journal of Human--Computer Interaction_ 40, 2 (2024), 441--456. doi:10.1080/10447318. 2022.2121038 

- [107] William B. Stiles. [n. d.]. https://wbstiles.net/session_evaluation_questionnaire. htm 

- [108] William B Stiles, Shirley Reynolds, Gillian E Hardy, Anne Rees, Michael Barkham, and David A Shapiro. 1994. Evaluation and description of psychotherapy sessions by clients using the Session Evaluation Questionnaire and the Session Impacts Scale. _Journal of Counseling Psychology_ 41, 2 (1994), 175--185. doi:10.1037/0022-0167.41.2.175 

- [109] S. Shyam Sundar and Jinyoung Kim. 2019. Machine Heuristic: When We Trust Computers More than Humans with Our Personal Information. In _Proceedings of the 2019 CHI Conference on Human Factors in Computing Systems_ (Glasgow, Scotland Uk) _(CHI '19)_ . Association for Computing Machinery, New York, NY, USA, 1--9. doi:10.1145/3290605.3300768 

- [110] Ella Tallyn, Hector Fried, Rory Gianni, Amy Isard, and Chris Speed. 2018. The Ethnobot: Gathering Ethnographies in the Age of IoT. In _Proceedings of the 2018 CHI Conference on Human Factors in Computing Systems_ (Montreal QC, Canada) _(CHI '18)_ . Association for Computing Machinery, New York, NY, USA, 1--13. doi:10.1145/3173574.3174178 

- [111] Dorthe Kirkegaard Thomsen and Svend Brinkmann. 2009. An Interviewer's Guide to Autobiographical Memory: Ways to Elicit Concrete Experiences and to Avoid Pitfalls in Interpreting Them. _Qualitative Research in Psychology_ 6, 4 (2009), 294--312. doi:10.1080/14780880802396806 

- [112] Charles Tilly. 2006. Why? What happens when people give reasons... and why. _Princeton: Princeton University Press. Weinberger, M., Oddone, EZ, Henderson, WG, Smith, DM, Huey, J., Giobbie-Hurder, A., & Feussner, JR (2001). Multisite randomized controlled trials in health services research: scientific challenges and operational issues. Medical Care_ 39, 6 (2006), 627634. 

- [113] David Traum. 2017. Computational approaches to dialogue. _The Routledge Handbook of Language and Dialogue_ 1 (2017), 143--161. 

- [114] Johanne R. Trippas, Damiano Spina, Lawrence Cavedon, Hideo Joho, and Mark Sanderson. 2018. Informing the Design of Spoken Conversational Search: Perspective Paper. In _Proceedings of the 2018 Conference on Human Information Interaction & Retrieval_ (New Brunswick, NJ, USA) _(CHIIR '18)_ . Association for Computing Machinery, New York, NY, USA, 32--41. doi:10.1145/3176349.3176387 

- [115] Lev Velykoivanenko, Kavous Salehzadeh Niksirat, Stefan Teofanovic, Bertil Chapuis, Michelle L. Mazurek, and Kevin Huguenin. 2024. Designing a Data-Driven Survey System: Leveraging Participants' Online Data to Personalize Surveys. In _Proceedings of the 2024 CHI Conference on Human Factors in Computing Systems_ (Honolulu, HI, USA) _(CHI '24)_ . Association for Computing Machinery, New York, NY, USA, Article 498, 22 pages. doi:10.1145/3613904.3642572 

- [116] W3Schools. 2024. HTML iframe tag. https://www.w3schools.com/tags/tag_ iframe.asp. [Accessed: 28-Jun-2024]. 

- [117] Marilyn A. Walker, Diane J. Litman, Candace A. Kamm, and Alicia Abella. 1997. PARADISE: a framework for evaluating spoken dialogue agents. In _Proceedings of the 35th Annual Meeting of the Association for Computational Linguistics and Eighth Conference of the European Chapter of the Association for Computational Linguistics_ (Madrid, Spain) _(ACL '98/EACL '98)_ . Association for Computational Linguistics, USA, 271--280. doi:10.3115/976909.979652 

- [118] Tom Wengraf. 2001. _Qualitative Research Interviewing: Biographic Narrative and Semi-Structured Methods_ . SAGE Publications Ltd. 424 pages. 

- [119] Richard L West, Lynn H Turner, and Gang Zhao. 2010. _Introducing communication theory: Analysis and application_ . Vol. 2. McGraw-Hill New York, NY. 

- [120] Lawrence R Wheeless. 1976. Self-disclosure and interpersonal solidarity: Measurement, validation, and relationships. _Human Communication Research_ 3, 1 (1976), 47--61. 

- [121] Senuri Wijenayake, Niels van Berkel, and Jorge Goncalves. 2020. Bots for Research: Minimising the Experimenter Effect. In _Adjunct Proceedings of the ACM SIGCHI Conference on Human Factors in Computing Systems_ (CHI'20 EA). 1--8. 

- [122] Alex C. Williams, Harmanpreet Kaur, Gloria Mark, Anne Loomis Thompson, Shamsi T. Iqbal, and Jaime Teevan. 2018. Supporting Workplace Detachment and Reattachment with Conversational Intelligence. In _Proceedings of the 2018 CHI Conference on Human Factors in Computing Systems_ (Montreal QC, Canada) _(CHI '18)_ . Association for Computing Machinery, New York, NY, USA, 1--13. doi:10.1145/3173574.3173662 

- [123] G.B. Willis. 2004. _Cognitive Interviewing: A Tool for Improving Questionnaire Design_ . SAGE Publications. 

- [124] Jacob O. Wobbrock, Leah Findlater, Darren Gergle, and James J. Higgins. 2011. The Aligned Rank Transform for Nonparametric Factorial Analyses Using Only 

CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Jacobsen et al. 

   - Anova Procedures. In _Proceedings of the SIGCHI Conference on Human Factors in Computing Systems_ (Vancouver, BC, Canada) _(CHI '11)_ . Association for Computing Machinery, New York, NY, USA, 143--146. doi:10.1145/1978942.1978963 

- [125] Kevin B. Wright. 2017. Researching Internet-Based Populations: Advantages and Disadvantages of Online Survey Research, Online Questionnaire Authoring Software Packages, and Web Survey Services. _Journal of Computer-Mediated Communication_ 10, 3 (07 2017), JCMC1034. doi:10.1111/j.1083-6101.2005.tb00259. x 

- [126] Ziang Xiao, Michelle X. Zhou, Wenxi Chen, Huahai Yang, and Changyan Chi. 2020. If I Hear You Correctly: Building and Evaluating Interview Chatbots with Active Listening Skills. In _Proceedings of the 2020 CHI Conference on Human Factors in Computing Systems_ (Honolulu, HI, USA) _(CHI '20)_ . Association for Computing Machinery, New York, NY, USA, 1--14. doi:10.1145/3313831.3376131 

- [127] Ziang Xiao, Michelle X. Zhou, and Wat-Tat Fu. 2019. Who should be my teammates: using a conversational agent to understand individuals and help teaming. In _Proceedings of the 24th International Conference on Intelligent User Interfaces_ (Marina del Ray, California) _(IUI '19)_ . Association for Computing Machinery, New York, NY, USA, 437--447. doi:10.1145/3301275.3302264 

- [128] Ziang Xiao, Michelle X. Zhou, Q. Vera Liao, Gloria Mark, Changyan Chi, Wenxi Chen, and Huahai Yang. 2020. Tell Me About Yourself: Using an AI-Powered Chatbot to Conduct Conversational Surveys with Open-ended Questions. _ACM Trans. Comput.-Hum. Interact._ 27, 3, Article 15 (2020), 37 pages. doi:10.1145/ 3381804 

- [129] Brahim Zarouali, Evert Van den Broeck, Michel Walrave, and Karolien Poels. 2018. Predicting consumer responses to a chatbot on Facebook. _Cyberpsychology, Behavior, and Social Networking_ 21, 8 (2018), 491--497. 

- [130] Yunfeng Zhang, Q. Vera Liao, and Biplav Srivastava. 2018. Towards an Optimal Dialog Strategy for Information Retrieval Using Both Open- and Close-ended Questions. In _23rd International Conference on Intelligent User Interfaces_ (Tokyo, Japan) _(IUI '18)_ . Association for Computing Machinery, New York, NY, USA, 365--369. doi:10.1145/3172944.3172998 

- [131] I. uka and A. Njegus. 2021. Conversational Survey Chatbot: User Experience and Perception. In _Sinteza 2021 - International Scientific Conference on Information Technology and Data Related Research_ . 322--327. doi:10.15308/Sinteza-2021322-327 

## **A Appendix** 

## **A.1 Tasks** 

Below we provide the informational text for each task that was shown to the participants for each of the three stages. In Table 8, each image/video for each research stage is shown along side the description. 

_A.1.1 Exploration._ For this first stage, we are interested in understanding your overall experiences with technology and how it affects your well-being. You will be shown three different images depicting situations where technology may be part of your daily life. Afterward, you will be asked questions about these situations. 

_A.1.2 Requirements._ For this stage, the goal is to understand the desires and expectations you have for improving current or future technologies. We want to learn about your needs, goals, and frustrations with the technologies you use in your life. You will be shown three different images depicting situations where technology may be part of your day. Afterward, you will be asked questions about these situations. 

_A.1.3 Evaluation._ In this stage, we will collect your feedback on a specific solution for managing technology use: the 'Do Not Disturb' feature for Apple iOS. You will now be shown a video about this feature. Please watch the video in its entirety. While watching, please consider how this feature may impact your life and the technologies you use. 

## **A.2 Example Responses for the Gricean Maxims** 

_A.2.1 Relevance._ <u>Relevance score of 0: "It is a tool, and should be</u> treated as such" 

<u>Relevance score of 1: "just random posts or news"</u> 

<u>Relevance score of 2:</u> "It changed my mood for the rest of the afternoon because my mind went to work when it should have been on my family. I was upset at myself for checking my phone and taking my time away." 

- _A.2.2 Specificity._ Specificity score of 0: "Yes, I have" 

- Specificity score of 1: "I don't want to get sidetracked from what 

- is really important." 

- Specificity score of 2: "Recently, I was away for the weekend 

- with my family enjoying quiet time at the lake. I checked my phone and saw I had a work related email that needed my attention. I spent 30 minutes away from my family while I went to handle the situation. I was upset and stressed that I had to do this on a Saturday while I should have been enjoying fun time with my family." 

- _A.2.3 Clarity._ Clarity score of 0: "inconvebient" and "NA" Clarity score of 1: "Sticking with what works" Clarity score of 2: "At work, they have many different platforms 

- that they use for communication, meetings, tracking training, tracking schedules, calendars, etc. They also keep updating the program we use for patient care charting so there are new or different boxes to fill out all of the time." 

## **A.3 Calculating Smoothness from SEQ** 

_smoothness_ =<sup>_easy_+ (8 -</sup><sup>_tense_</sup><sup><u>) +</u></sup><sup>_<u>pleasant</u>_+</sup><sup>_smooth_+ (8 -</sup><sup>_uncomfortable_</sup><sup><u>)</u></sup> 5 

## **A.4 Chat Excerpts** 

_A.4.1 Participants Demanding More Specific Questions._ 

|**Chatbot:**|Hello, I would like to discuss the impact of technology<br>on stress. Have you experienced technology having a<br>stressing effect on your life?|
|---|---|
|**User:**<br>|Sometimes<br>|
|**Chatbot:**|Thank you for sharing that. Can you explain when<br>you typically experience this stress and what usually<br>triggers it?|
|**User:**|First, give me a few examples|
|**Chatbot:**|Of course. For example, some people feel stressed due<br>to a high volume of work emails, constant notifications<br>from apps, difficulties in learning new software, or pres-<br>sure to stay connected online all the time. Do any of<br>these resonate with your experiences?|
|**User:**|No|
|**Chatbot:**|Thank you for clarifying. Can you explain what specific<br>situations or interactions with technology cause you<br>stress?|
|**User:**|It's still hard to answer that since it is a broad question<br>that could mean anything|
|**Chatbot:**|I understand. Let's narrow it down. Can you describe a<br>recent situation where interacting with technology left<br>you feeling stressed or overwhelmed? What specifically<br>caused that feeling in that instance?|
|**User:**|Narrow it down further please|
|**Chatbot:**|Absolutely. Have you ever felt stressed when using<br>your smartphone specifically? If so, what in particular|



CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Chatbots for Data Collection in Surveys 



<!-- Start of picture text -->
Home Public Work<br>Exploration<br>Image shown hy: Me WAZ5 a Ses ce<br>: yy, Mz<br>Consider how different technologies Consider how your work life is<br>Consider how technology affects<br>affect your life when you are at affected by technology, including<br>Text description your experiences and activities<br>home, and how this impacts both situations where you use it or are<br>when you are outside in public.<br>you and the people around you. influenced by it.<br>Requirements<br>= et ore<br>Image shown<br>| ' OTN : 2 Be. "e<br>Consider how your life when at Consider when you are outside in<br>Consider how your work life is<br>home is affected by technology, and public, and think about what<br>being affected by technology, and<br>Text description think about what improvements improvements could be made to<br>what can be done to current or<br>could be made to current or future current or future technology in a<br>future technology in a positive way.<br>technology in a positive way. positive way.<br>Evaluation<br>Video<br>UseDot gy at<br>Control Center | <br>Table 8: Table showing the different images/video shown for each research stage.<br><!-- End of picture text -->

caused that stressa"such as a specific app, feature, or notification? **User:** Over my phone, yes. So much that it would sound overrated calling it a 'smartphone' since it's not as smart as industries claim it to be. It's more like an app phone or feature phone and nothing else. Considering how every app and photos / videos takes up huge chunks of storage space and the battery life is terrible and faulty. For example, I would have to constantly clear up space for any new apps I'd want to install. Another example is how my phone would instantly turn itself off when my battery reaches 30% battery while playing a game. No low battery indicator warnings or anything. And the app store is mostly junk apps that are filled with crappy games and poorly made applications infested with ads and in-app purchases just to get it to work. 

_A.4.2 Clarifying Technology Features as Part of the Evaluation Phase._ **Chatbot:** Got it. So, prioritizing checking emails on your own schedule rather than being interrupted by alerts might be beneficial. Could you describe any potential downsides or challenges you might foresee with leaving "do not disturb" on all the time? **User:** I might not see calls and texts? Do calls still come through with it on? **Chatbot:** Calls are silenced when "Do Not Disturb" is on. Given that, how would missing potentially important calls or texts impact your stress levels or daily routine? **User:** I would want to silence notifications but not calls. There's probably a way to do that. 

CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Jacobsen et al. 

- **Chatbot:** Yes, you can customize "Do Not Disturb" settings to allow calls from certain people. Could you clarify how having this level of control over notifications might influence your stress levels with technology? 

- **User:** Less junk taking my attention away from what I am concentrating on would help stress levels for me. 

_A.4.3 Returning to Past Points._ After the participant was being asked about some possible ways to change technology to better fit your needs, and how they could believe technology could be improved to decrease its stressing effects on their life. 

- **User:** Apps that remind users to stay in the present and interact with people through other means than just technology. Stop giving customer service jobs to AI bots. Always allow pressing zero to talk to a human. 

- **Chatbot:** Thank you for sharing that. Regarding apps that remind users to stay present, can you clarify what kind of reminders or features you would find most helpful in such an app? 

- **User:** Maybe like daily affirmations sent via SMS or within an app to remind people to partake in human interaction. Be kind, compliment someone, strike up a conversation with someone you might not otherwise talk to. 

- **Chatbot:** I see, daily affirmations encouraging human interaction sound beneficial. Can you provide an example of a situation where receiving such a reminder would have significantly impacted your day positively? 

- **User:** Not specifically, I think it would just be nice for people to have that reminder once in a while so they don't get so focused on their screens, particularly when out in public. 

- **Chatbot:** Got it. Shifting to your point about customer service AI bots, can you explain in more detail why you find AI bots stressful and how this stress arises? 

- **User:** AI is taking over too many jobs that people need. If you take away lower level jobs from people who don't have any education or experience beyond what they're already doing for work, it becomes a problem when that person can't afford new training and/or provide for their family. 

- _A.4.4 Creating In-Conversation Realisations._ **User:** Sometimes, I use technology to escape reality. But in all honesty, sometimes not having that escape causes me anxiety. I probably wouldn't struggle with that anxiety if I had a healthier coping mechanism to deal with dayto-day stress that makes me feel the need to escape. 

- **Chatbot:** I appreciate your openness. Could you elaborate on why you feel the absence of that technological escape increases your anxiety? 

- **Removed:** [16 messages back and fourth between the participant and the chatbot in between here] 

- **User:** I think it has helped a little. But I still think that technology overall has such a big influence on our lives, and is almost impossible to do away with entirely that there's really no escaping it... Ironically, I mentioned first that I use technology as an escape, but I suppose the reality is that there is no escaping technology. 

_A.4.5 Inquiring through Hypothetical Examples._ After the participant was being asked about some possible ways to change technology to better fit your needs, and how they could believe technology could be improved to decrease its stressing effects on their life. 

- **User:** I don't see how it can be improved relating to the stress it might cause people. I don't get stressed by technology. 

- **Chatbot:** Thanks for sharing that. Even if you donaTMt personally experience stress from technology, can you think of situations where others might feel stressed by it? Could you describe a specific scenario where someone might feel overwhelmed by technology? 

- **User:** A person unfamiliar with it at a new job would be overwhelmed, I'm sure. They would require the correct training by a patient instructor. If an app on the device were installed that taught them how to use the device for the task they were working on, that would be helpful. 

- **Chatbot:** Thank you for that scenario. Can you describe in more detail what aspects of using new technology might overwhelm someone in a new job? For instance, what specific tasks or features might cause confusion or stress? 

- **User:** If someone had never used Excel, they would have no idea where to begin. They definitely would need prior instruction. 

- **Chatbot:** That makes sense. Can you give an example of how a lack of knowledge in Excel specifically might impact someone's workday? What kinds of problems or stress might they encounter because of this? 

- **User:** If they lied when they were hired for the job and said they were proficient in Excel, then were given an assignment on their first day to produce a spreadsheet detailing the company's finances, that would be stressful. I think it would ruin their work day. 

- **Chatbot:** Thanks for that detailed example. In such a stressful situation, what kind of support or resources do you think would make the most significant difference for that person? Can you describe any particular tools or assistance that could help alleviate their stress? 

- **User:** If there were instruction in the Excel app, when you clicked one of the functions, if it gave more information on how to use it, that might be helpful. Or an instructional video inside the app would help. 

- **Chatbot:** That sounds like a useful solution. Can you elaborate on how you envision the instructional content being integrated into the Excel app? For example, what specific features or types of information would be most helpful in reducing stress for the user? 

- **User:** If there were a separate part of Excel, if when you opened the application, you have a choice to select "instruction" or a manual. 

- **Chatbot:** I see. Could you describe in more detail how this instructional section might look and operate? For instance, what kind of content should it include and how would it guide users through learning Excel? 

- **User:** It could be divided into the various functions of Excel. A quick short video showing what each button is for, 

CHI '25, April 26-May 1, 2025, Yokohama, Japan 

Chatbots for Data Collection in Surveys 

and the capabilities of it. Like a short "chapter" for each function, either text or video. 



---

## Extracted Figures

![Img 1](img_1.png)

![Img 2](img_2.png)

![Img 3](img_3.png)

![Img 4](img_4.png)

![Img 5](img_5.png)

![Img 6](img_6.png)

![Img 7](img_7.png)

![Img 8](img_8.png)

![Img 9](img_9.png)

![Img 10](img_10.png)

![Img 11](img_11.png)

![Img 12](img_12.png)

![Img 13](img_13.png)

![Img 14](img_14.png)

![Img 15](img_15.png)

![Img 16](img_16.png)

![Img 17](img_17.png)

![Img 18](img_18.png)

![Img 19](img_19.png)

![Img 20](img_20.png)

![Img 21](img_21.png)

![Img 22](img_22.png)

![Img 23](img_23.png)

![Img 24](img_24.png)

![Img 25](img_25.png)

![Img 26](img_26.png)

![Img 27](img_27.png)

![Img 28](img_28.png)

