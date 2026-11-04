# 智能纪要：Project Demo and Discussion 2026年11月5日

录音时间：2026\-11\-04 15:00 \- 2026\-11\-04 15:39

@说话人 1  00:00
Like also getting through it.We're doing great.Good.You're, you all are so close.You all graduate after this, right?Are you getting excited?Yeah, I think it'll hit us when we're like right there.We'll be like, oh, we're graduating.Yeah, when you have a lot of work between now and there, it just gets stressful.Yeah, it's okay.Good.And I, I, so I have Rosie here.I don't, I think Karen is busy.I don't think she'll be able to pop in.But Rosie, she's not feeling great, so she's gonna stay off the camera.But she may have some thoughts and questions.Okay, and then we have one more person that's not here.Yeah, we're waiting on Brandon. I think he's coming soon.

@说话人 2  00:42
Alright, no worries.How's the project going?Any questions or anything?Not so far.I don't think we do have a demo to show you guys today.So I think it's gonna, Eric is gonna show on his screen and wouldn't go through it.Quickly and see if there's any feedback or anything you want us add.There are some things we still need to fix, but I think we have a working model so far.Hi, Brandon, good to see you as well.Hello.Alright, well, yeah, whenever you all are ready.I didn't have anything new for you or anything, so.

@说话人 3  01:28
Yeah, so today we have a demo for you.So here's what the website looks like right now.And we have four tabs here, like we can create a chat and we can upload new files here. And here are the.What existing upload files here.We create a data set here and here is the SE setting.In this setting, we can use different AI model here, like thought, GBT, open air, and deep seek.So we highly recommend you to use this thought GBT.So we think using this solid GPT, we can upload the student record here and privately, because solid GPT will like keep the p 3.So the students records are P3 data so that GPD can protect the P3 dicta under private.Okay, so and here is a feature toggle called, actually, do you mind, would it be okay if we recorded this?Karen just want to see the demo and she's not able to be here.Is we won't like distribute it or anything like that? Is that okay?

@说话人 1  02:55
Yeah, yeah, yeah. Let me do that real quick. Hum.

@说话人 3  03:02
Alright, and keep going.Yeah, so we can ask the AI some question here. Like, let me copy.Oh, cool.Oh, interesting.Yeah, so right now the workflow is we ask the AI with the natural language and AI will generate a sequel to query in this data set and return the results. If we.Turn on this feature, Toggle AI can see the results and summary, do some summary with the this results.We, yeah, from the data set and if we turn off this feature, Toggle AI can only see the SQL query here and it will return the results from.The data sets directly.And here we can switch different am model here.Wait, I thought that we were using the ChatGPT or the zot GPT model. Yeah, is okay.

@说话人 1  04:23
So why does it say deep seek?So I guess maybe this is so is deep seek its own model?Or is it that, sorry, that maybe a dumb question.Yeah, Deep Seek is a demo just of, it's a AI model just for the demo.So in the production environment, we highly recommend you to use solid GBT.

@说话人 3  04:47
Because in my environment, I didn't deploy Zod GPT, but Molly, Mo, I think Molly are using this Zod GPT model.Okay.Yeah, within Zod GPT, there is different models you can specifically use.Right now, how I set up on my computer is I'm using it with Claude on it.

@说话人 2  05:11
And I think as students, we get like 100 dollar credits.That's why we were able to test and deploy this on my computer.But yeah, I think on Eric, he only set it up with deepseek. Okay, and Molly, create another dummy file.

@说话人 3  05:32
For our to test the upload function.And wait, Eric, can you go over like in the chat when you ask the question, there's a button where you can download the, oh yeah, Excel.After we, after AI replies the response, we can download the.

@说话人 4  05:53
Excel or CSV file here.Like, I don't know if they can, you guys see the pop up?No, yeah, they can't see it.So you need to change your window for sharing. Yeah, or I can do.

@说话人 3  06:21
Can you see my Chrome right now?I'm, I think we can only see, we see your icon, right? Oh, okay. Try to upload this.

@说话人 4  06:36
Yeah, so here are the CSV file.Looks like.Cool.And we can also download the Excel file here.Okay.So then this way, if you ask for like a specific query, like, oh, everyone who went to bagel breakfast, who's from like this specific department.Once it looks for that, it can also create just that spreadsheet just for that question.But you can also, if you just go to the full data set, if you want the full data set, you can also download the full data set over here. Yeah. Okay. Oh, cool. Yeah.

@说话人 2  07:17
Yeah, the full data set is pretty much the compile data set that was generated. Okay, cool.

@说话人 4  07:30
Yeah, here's a full data set here.Okay, great.Okay.Yeah, so whenever you upload a new, if you go to upload, whenever you upload like a new, you know, event format, if it's from 12,20 or campus groups, it'll populate here and it'll have you fill out the event name.Like if you wanna change any of the details yourself.And then once you're ready to add it to the full data set that we're keeping for you in this, that.

@说话人 2  08:00
Or the app is keeping for you.After you fill out this information, you commit, it'll add it to the full data set.Great.Okay.And I believe that if you were to re upload the same file, it would flag it as a duplicate.So it won't wouldn't actually get added to the compile data sheet.But there is a bug right now that we notice.If we were to make a minor changes to one of files and re upload, that would actually get added.So that's something we're looking to fix in the next sprint that would add it as kind of like duplicates then.Yeah. Okay, great. That's something we need to work on.

@说话人 1  08:45
What about searching by like, so like in some of the original data that I gave to you, it had some intentional like missing data is what happens if we have like a student record that's in more than one event, but maybe it's like.Missing some data or something like that.Is it able to kind of flag data that way?

@说话人 4  09:12
Think so, yeah, we can like if so if you ask if we need like an example, so if we say, I guess prob the sample data that you gave us, that was.What's it called?It's like not actually the real dummy data.Did any of the dummy data have that issue?Or I think there was some missing data in there.I think I put some in there just to kinda, cuz that's more realistic to what her data is like.Okay.Okay.So then let's just open up one and see if there's a missing one and we can ask it and see what happens. Yeah.

@说话人 2  09:57
So all the data that were provided from the sample data were actually compile to the compile data sheet.So I think it might have missed like the.Oh, so that filled in any of the gaps that it had.Yeah, cuz like every single role was actually imported to the compile data sheet.From cuz I the under the data area that is specify how many roles are in each file.And then we compare that to the compile data sheet and imported a total of 299 roles, I believe, or 293 roles.And I added up all the numbers from the roles, from all these data and.It was exactly 293.

@说话人 2  10:40
Okay.So what are these, the flags there?Like, what are those then?Those, I believe it's duplicates or not duplicates, maybe missing records, right? Eric or Brandon? Yeah, I think so.

@说话人 1  10:58
Okay, so that's something we need to look into still.Yeah, here.Okay.Yep.But that's what we have so far.Okay.So how is this?So I kind of remember early on you talked about like this would be something that's tied to a computer, I think.

@说话人 2  11:20
It w.Is that still?It would be something that would be loaded on my computer or.Okay, very good.So what we're thinking is that possibly, I think the week before our capstone showcase on December 7th, we're gonna see if we could help you set it up on your computer and train the staff how to use it.Whether that's in person, cuz we're on campus on Monday and Tuesday, but we're not sure if that works for your schedule.Preferably like after 4, but if not, then that Wednesday we could probably be on zoom and help you set it up and walk you through it.The only thing that we might require is for you to download Docker on your computer.We're not sure if you guys use a Mac or Windows right now.

@说话人 2  12:07
Windows and Windows.Okay, so we're gonna create like a guideline on how to download Docker and stuff and then it'll make it easier during the meeting to help you guys set it up.I'm not sure that day works for you, but we're trying to go for December, November 30th through December 2nd.

@说话人 1  12:29
I think November, so I can be on campus late on that Monday.I just need to plan ahead.So do you want to go ahead and plan an in person meeting at 4 p.M.On Monday the 30th?Yeah, so we have class on Mondays, but usually that class.

@说话人 2  12:49
We're allotted some time to meet and with the professor for like 30 minutes and do our project on our own.So we can meet you probably like around 4:30 if that's.Works with your schedule.I just gotta plan ahead, which I can do.Okay, I better do it for.I'm putting it in my calendar right now, but I put it for 4:30 a.M.So tentatively, we're gonna say 4:30.If anything changes, will email you. But for now, 4:30 on November 30th. Okay. Okay.

@说话人 1  13:22
Yeah, is there any questions or concern you have about the current system so far?I don't think so.I mean, one of the things I'm, I guess, you know, some of this, I'm wondering if I'm going to be able to like, you know, like once I get my hands on, I can play with it a little and I think I'll have more.

@说话人 1  13:41
Thoughts, but is there any like issue with like the fact that 1220 has, sorry, I'm also doing, I'm multitasking.It's a bad idea.Like records that are imperfectly matched.Is it able to do anything?So like if I, for example, let's say that I put in your net ID, well.Actually, let's start with this.1220 has emails, but it doesn't have net IDS or student IDS.Is that, is it able to match that?So like a student on 1220 that doesn't have a student ID number in 1220, is it able to connect that to a student record from campus groups where there is a student ID number.

@说话人 3  14:28
Yeah, we so our system right now will match the net ID first and if the net ID is missing, we will match the email.But no student ID, we will only match net ID and email.Yeah, that's perfect.Yeah, we'd like to rely on the student ID, little or nothing. So that works great.

@说话人 1  14:53
It looks really cool.Like, I'm excited to chat with it.I don't think I have any questions.Rosie, I know you're not feeling great, but do you have any questions or thoughts?What you ask is actually the one I was thinking about to like trying to match them from.

@说话人 2  15:12
One to the other.So that be that's really cool that I could do that.It's looks like great.Yeah, good work.Do you have any more questions for us?Yeah, no questions, but I think we're still looking into what we currently have and fixing any bugs we come across and potentially add more features in the next Sprint if there's time.There is a few list of things we potentially wanna add.And I think if their time permits, then a staff log in.But I think that is in Sprint No. 3 that we might not be able to get to, but we're not too sure yet, but we'll keep you updated. Okay.

@说话人 4  15:59
Yeah, well, what else do you need from me and my team at this time?I don't think we need anything.Eric, Brandon, Zhen, do you have anything?I don't think so.I think we just mainly wanted a demo and then give you an update on, you know, what we're trying to fix some bugs, right?And then we're thinking about doing those features. So if you had.Any ideas of things you want to add?And then, yeah, I think our data is good.I think that's it.That's all I can think of. Okay. Yeah, well, yeah, this looks great.

@说话人 1  16:44
I don't think I have anything further either.So I, unless there's more, I can let you work on this for the next two weeks.And then I think the next time we're meeting is not next week, but the next week.That works for you all the 18?

@说话人 1  16:59
Yes.Okay.Thank you.Alright, well, good work, everyone.Thank you.Thank you.And again, I'll give you some time back cuz I know that you're busy students and can use it.For many different things.Yes.Thank you.Thank you.Alright, nice to check in with you all and thank you for your work.This looks great.Thank you.Alright, bye, everyone.Bye.Okay.Okay, here's what the API usage look like. Oh dang, 6,000.

@说话人 4  17:31
Oh, is that good or bad?Is this token?Yeah, I think that's pretty good.She said somebody use 26 and she thought that was really good already.26,000.Are we using too little?I think it's because I test a lot here.Okay, okay, okay.I think we're done.I think we're good. Okay, so then we just submit it.

@说话人 3  17:52
Submitted the link, but we already submitted the link.Oh, we already she, I think she can say you can resubmit it, but the link is.

@说话人 4  18:00
Oh, the link updates.Okay, I think that's fine.Then go to the submission, click on the link and see if that's in there. It should be in there.

@说话人 3  18:43
What the reason, what, why here is no, I guys here would have, yeah, cuz we need upload or drag a file.But I remem we, I remember we have already upload. It's.

@说话人 4  19:00
I don't think we did.Cuz remember at the end of class, we're like, oh, we can submit it after the demo.Oh, okay, cool.Okay.So then just add the link.Okay, cool.Okay.I'll put it later.Can you guys hear us, Jen?Hello.Oh, I was just talking to Brandon about what we have so far and like.

@说话人 2  19:22
If there's any issues you guys ran into when you were like playing with the system, because I think there's a few things I noted on my end that I think we should fix.So one of them being like, yeah, the flagging, flag, flag, flagging, the flagging that she mentioned.

@说话人 4  19:44
Yeah, I think that's a missing information from those data sets, right?Yeah, actually, I didn't know what flag is.I didn't test it.And okay, we do have flag.We should make it so that they can click on it and see like what we're flagging and why we're flagging it. Yeah, yeah.

@说话人 2  20:06
Let me open up the actual data set.So when I calculated like, yeah, the rows, they imported everything over.So there might be like certain rows that should been flagged.I don't know what that. So that's something we need into.Another thing is that when you upload a new sheet into the data, you know how you have to pre fill out the form.Let's say they make an a mistake like instead of bagel breakfast January, they put bagel first.February or something, right?And there is no way for once you upload it to go back and edit that or so that's something we probably still need to fix.

@说话人 5  21:10
That's a good point.And then maybe also the delete flow to when we delete a data set.Yeah, yeah, that was something that we need to be able to do too. Yeah.

@说话人 2  21:26
We can add it to our backlog. The lead data set, the flagging, make sure.

@说话人 4  21:44
Was there anything all she mentioned or she asked us about?No, I think she mentioned the missing like we're like you already said.So if a record is kind of missing some information, what does it do?So then it should flag it, right? But should it flag it and not?Add it to the data set then, right?And let them correct it first.Yeah, I think that's what, well, or should it just, okay, add it and just say we didn't add these.Okay, so I'm looking at the one that we uploaded.

@说话人 2  22:24
The LinkedIn info session.So there's three flags for that, right?And there's 34 rows.Yeah, so I'm trying to distinguish how, what the 3 num No. 3 means.Cuz I guess on the sample data, one person is missing their email.But I don't see any other missing logic or missing information here. So I don't know how they got 3 from.

@说话人 2  23:52
Did you guys do your demo already?Yeah, yeah, we just finished it.Oh, how did it go? That's good. That's good. Yeah.

@说话人 4  24:23
Oh, Molly, so it said in source row 8, the net ID was blank, the email was blank.And since both of those were blank, then this row can't be linked to a person.So the third one is kind of just like the same as 1 and 2. What was the numbers again?

@说话人 2  24:45
I mean, what, what row?Row No. 8.Okay.Row No. 8, what did it say again?I said no net ID and no email. No net ID.I only see no email cuz this doesn't have 12,20 or whatever, doesn't have.Oh yeah, so then I guess it's.So it's no email, there's no net ID because there is no net ID. Yeah, net ID blank. Email blank. No net ID.

@说话人 2  25:20
Yeah, I sent a screenshot in the discord chat.Okay, so for 1220, you know how there's no net ID, right?Currently, the system raised only the email. Hum, is it link to.What is exactly linked to, I guess, what do you mean?What is it linked to?Like when it adds it to the actual like compile data sheet.So the hub gets a net ID from the email. So this will has no ID.

@说话人 4  26:06
Yeah, I think cuz since there's no email, it can't get the net ID.So then it's complaining for them for No. 1 and No. 3, basically.Okay, so I think for those, she did she want us to flag it so she could correct it.

@说话人 3  26:23
Oh, I don't remember what she said.I think she just ask like what happens and I don't remember what we said. Yeah.

@说话人 4  26:44
Cuz that would be an error now.Yeah, but I feel like if if, you know, if it's missing stuff, maybe it shouldn't be added at all.So we can have it like pull those out and then we can just have it show it to her or we could also have it show it to her and let her edit it herself.

@说话人 5  27:05
And then commit it to the database.Maybe we can show some message when in this upload tab.Yeah, yeah, I think that might be the easiest if we can surface like a message like what Eric mentioned and then.If she wants to correct it, then she can correct it in Excel, like manually before dragging and dropping into our website.Okay.Yeah, make so that we don't have to build like an editor.Yeah, I mean, that could be like one of the FEA.I think we listed like four features that we're thinking about for Sprint 3.

@说话人 4  27:48
But I think like one was like the login and one was, I don't remember, but like technically we could make the editing thing a feature if we wanted instead of, yeah, okay.

@说话人 2  28:11
So right now, yeah, it does get added to the compile data sheet.So I guess when you drag, one thing we should probably do is flag it.So the person who is dragging and dropping it can.Either decide whether to add it or not.Yeah, or make changes if needed or should we just like let them say yes or no and then they edit it on their own on Excel before they re upload it. Cuz what if they like upload it and then.You know how we ran into the issue where like, oh, there were minor changes and they actually add their email and re upload it will add it twice to the power data sheet.Hum. So I don't know which is the best approach.

@说话人 5  29:15
So what if we can, for example, you upload one data set and then we keep track of the rows it gets map to.So like data set a is rows 1 through ten.And if they try to re upload the data set with the same identifier, then it overwrites rose 1 through 10 to account for the duplicates. And if they upload like data set B.It will append rows 11 through 20 right below.But when data set a is deleted, then rows 1 through 10 are gone.So kind of like maintains a mapping, but I'm not sure if that's the right approach here. Maybe if each row contained like some identifier.Signaling which data set it came from.And then when they want to delete a data set, we just scan the database for all the rows containing that identifier.Might be slow with the scan, but it could work.

@说话人 2  30:54
Yeah, I don't know what's the best approach, but that's potentially one we could look into. I don't know how difficult it would be, though.

@说话人 3  32:09
Yeah, I think we can discuss with, maybe we can discuss later for this question.Okay, I'm also trying to figure out like what the other flags are and like.

@说话人 4  32:33
I don't know, like there's one for Edwards Live Science.

@说话人 4  32:46
Yeah, I feel like if we have the warning show up when they're trying to upload it and then ask them, okay, do you still want to upload it or no?

@说话人 2  32:54
Like don't upload it yet, then we could probably get rid of that flag feature too.I think like originally in her proposal, she wants us to be, I will base on like what she told us on her first proposal was that she wants the person input.Uploading or like work on this, the ability to make changes or something or take note of the flags.Yeah, so then if we decide to build out instead of just the warning, we have the warning and then be like, okay, do you want it?

@说话人 4  33:35
Edit this, but I don't know cuz that like you said, like that might if we change it a little bit, it might just put the whole thing in again when it shouldn't.I guess I could do a little bit more research and see the best approach.Cuz I feel like, yeah, the issue is like, yeah, if there's a flag.

@说话人 2  33:58
And they re upload it, then it will get added again, right?So they do you want them to be able to correct that flag before it gets uploaded? Yeah, probably so.

@说话人 4  34:18
It doesn't need if they don't wanna correct.Like what if they just wanna upload everything and then just they like can't find the information for that one person.So then they just decide to exclude that one.But I guess they could just edit it on the Excel directly.If they edit on the Excel directly, then they wanna re upload that, right?Yeah, it's gonna be a duplicate.So, well, yeah, so I think right now we have it as two steps.We have upload and then you like check, you know, the event information and then you click commit to the database.So if we upload it and then we have the warning pop up hum before they click commit, then it wouldn't have put it inside the data.

@说话人 2  35:00
Save.Are we gonna give them the option though to be like, bypass the flags?Cuz like, what if like, yeah, it's missing an email and they can't figure out the email.So s, they'll probably still leave it empty, right?So they're gonna just bypass that flag and just click commit.

@说话人 4  35:21
Yeah, I think we can give them option.And then later when we, cuz we're also trying to work on letting them delete stuff too, if they wanted to delete it after it's been committed and they could delete it also too.Okay, I guess, yeah, that's what do you guys, what is I.

@说话人 2  35:43
Think that's okay with me?

@说话人 3  36:08
Yeah, I agree.

@说话人 2  36:23
Okay, so then besides that, is there anything else that we wanna think about right now?So that and the ability to delete files or delete a data set and.Yeah, I think that's pretty much it right now, unless you can think of something that comes up, you guys could just message us.Yeah, I think those are the two buggy things, right, that we're trying to do.Yeah, I don't.I don't.Was there another one?I think as of right now, just continue to play around with the software and see if there's any like test everything manually and see if there's any other bugs that we can address so we could write it all down and fix it. Okay.Yeah, I wanna s continue seeing if I run into any other issues. Okay.Okay, anything else you guys want to talk about?Nope, nothing for me.Alright, I guess we can meet her.Okay, we're gonna meet her on the 30th to help her set it up.Or yeah, I don't know. Cuz she said that she wanted to play.

@说话人 4  37:51
Like when she plays around with it, she might have more things, but we're not really letting her play around with it if we're giving it to her on November 30. But.That's fine.Yeah, that's the only thing I'm like, do we meet?Do, should we meet with her earlier so we can fix everything she tells us.Yeah, cuz she doesn't even have it installed yet, but I don't know, she seemed okay with just having it on the 30th too. Why? Don't know. Maybe we should've, I don't know.

@说话人 2  38:22
I mean, it could be our ongoing project after we graduate.Yeah, we continue to help her fix it if anything.Okay, you guys go then. Unless there's anything else you wanna talk about.

@说话人 2  38:46
Brandon, nothing from my end.Alrighty then.Thanks, guys.Awesome.Thanks, Molly.Thanks, everybody.Molly.Bye.Bye.You okay? Good luck in class today. Thanks. Bye bye.
> （注：部分内容可能由 AI 生成）
