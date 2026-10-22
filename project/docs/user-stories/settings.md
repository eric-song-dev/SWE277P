# Settings stories

Managing the AI models (LLM profiles) Chat can use. Format, stacks, helper profiles and recording:
[README.md](README.md). Window 1440×900 unless a story says otherwise.

On the replay stack the provider list includes "Demo (scripted)"; on main it does not. The test
profile "Unreachable" used below points at a closed local port, so its key never leaves the
machine: Name "Unreachable", Provider "Custom (OpenAI-compatible)", Base URL
`http://127.0.0.1:9/v1`, Model `test-model`, API key `sk-test-1111`.

### ST-01 Add the first AI model
- **Who:** the person setting up the Hub for the GPSRC office
- **Story:** As the person setting it up, I want to add the first AI model from the Settings page, so that staff can start asking questions without editing files.
- **Stack:** replay (Demo), before any profile exists
- **Acceptance criteria:**
  - With no model, Settings shows "No AI models yet. Add one to start asking questions." and an "Add AI model" button. The page header has no button yet.
  - "Add AI model" opens the "Add AI model" dialog with:
    - "Name", "Provider" (starting at "ZotGPT Gateway"), "Base URL", "Model" and "API key";
    - the switch "Allow sending query results to this AI", with "Lets the chat page's 'Let AI see the results' switch be turned on for this model." under it;
    - "Cancel" and "Save".
  - "Save" is disabled until the required fields are filled.
  - Choosing "Demo (scripted)" hides Base URL and API key and turns the switch on.
  - Saving Name "Demo", Model "scripted" closes the dialog and shows a "Demo" card with:
    - the tags "Default" and "Can receive results";
    - the lines "Demo (scripted)", "scripted", "No key saved" and "Not tested yet";
    - the buttons "Test", "Edit" and "Delete", with no "Make default".
  - After the save, the page header shows "Add AI model".
  - Chat then shows "AI model" with "Demo" and the question box.
- **Walk:**
  1. On a fresh replay stack with no profile (skip the README's `curl`), open Settings. Read the page.
  2. Click "Add AI model". Read the dialog and check Save.
  3. Choose Provider "Demo (scripted)". Check which fields remain and the switch.
  4. Type Name "Demo" and Model "scripted". Click Save. Read the card and the header.
  5. Open Chat and check the select and the box.

### ST-02 Each provider preset (URL prefill, sharing default)
- **Who:** the person setting up the Hub, choosing between providers
- **Story:** As the person setting it up, I want each provider choice to fill in its known address and a safe sharing default, so that I only type what is specific to us.
- **Stack:** replay (Demo); one look on main (DeepSeek), nothing saved
- **Acceptance criteria:**
  - Provider offers "ZotGPT Gateway", "OpenAI", "DeepSeek", "Custom (OpenAI-compatible)" and, on replay only, "Demo (scripted)".
  - Each choice sets the dialog as follows:

    | Provider | Base URL | Switch |
    |---|---|---|
    | ZotGPT Gateway | empty, required | on |
    | OpenAI | `https://api.openai.com/v1` | off |
    | DeepSeek | `https://api.deepseek.com` | off |
    | Custom (OpenAI-compatible) | empty, required | off |
    | Demo (scripted) | field hidden (no API key field either) | on |
  - Switching from OpenAI to Custom clears the OpenAI address. A URL typed by hand stays when switching to ZotGPT Gateway or Custom.
  - For a new non-Demo model, Save stays disabled until Name, Model, API key and (when required) Base URL are filled.
  - Saving DeepSeek with Name "DeepSeek Test", Model `deepseek-chat` and key `sk-test-1234` gives a card with "DeepSeek", "deepseek-chat" and "sk-…1234", without "Can receive results".
  - On main, Provider does not offer "Demo (scripted)".
- **Walk:**
  1. In Settings, click "Add AI model". Choose each provider in turn and read Base URL, its "*" and the switch.
  2. Choose OpenAI, then Custom, and read Base URL. Type `https://llm.example.edu/v1`, choose ZotGPT Gateway, and read Base URL.
  3. Choose DeepSeek and fill the fields one at a time, watching Save. Save "DeepSeek Test" and read the card.
  4. Delete "DeepSeek Test".
  5. On main, click "Add AI model", open Provider, read the options, and click Cancel.

### ST-03 Test a connection (pass, fail)
- **Who:** the person setting up the Hub, checking a new key works
- **Story:** As the person setting it up, I want to test a model and see a clear pass or failure, so that I find a wrong key or address before staff do.
- **Stack:** replay (Demo) for the failure and the Demo pass; main (DeepSeek) for a real pass
- **Acceptance criteria:**
  - "Test" is disabled while the test runs.
  - Replay: "Test" on "Demo" shows "Connected".
  - Replay: "Test" on "Unreachable" shows "Could not reach the AI provider. Check the base URL and your network, then retry." in red.
  - Main: "Test" on "DeepSeek" shows "Connected" within 30 seconds.
  - After a reload, each card shows its last result: "Last test passed <date and time>" or "Last test failed <date and time>".
  - Main: after a passing test, "Edit" → Model offers the provider's model names as suggestions.
- **Walk:**
  1. On replay, add "Unreachable" (see the top of this file).
  2. Click "Test" on "Demo", then on "Unreachable". Read each result.
  3. Reload and read both cards.
  4. On main, click "Test" on "DeepSeek", time it, and read the result. Click "Edit", open the Model suggestions, then click Cancel (do not save). Reload and read the card.

### ST-04 Edit without re-entering the key, then change it
- **Who:** the person maintaining the Hub, changing a model name
- **Story:** As the maintainer, I want to edit a model without retyping its key, and to replace the key when it changes, so that keys are typed once and never shown again.
- **Stack:** replay (Demo), with "Unreachable" from ST-03
- **Acceptance criteria:**
  - "Edit" opens "Edit AI model" with Name, Provider, Base URL and Model filled in. The API key field is empty, not required, and reads "Leave empty to keep the saved key. Saved key: sk-…1111".
  - Changing only Model to `test-model-2` and saving keeps "sk-…1111" on the card and resets the test line to "Not tested yet".
  - "Test" afterwards still uses the saved key: it shows the same "Could not reach the AI provider. Check the base URL and your network, then retry.", not a missing-key error.
  - Typing only spaces in API key and saving keeps "sk-…1111".
  - Typing `sk-test-2222` and saving changes the card to "sk-…2222".
  - The key is never shown: the field is always empty when the dialog opens, and `GET /api/llm-profiles` holds only the hint.
- **Walk:**
  1. Click "Edit" on "Unreachable". Read the fields and the key helper.
  2. Change Model to `test-model-2` and Save. Read the card. Click "Test".
  3. Edit again, type three spaces in API key, and Save. Read the hint.
  4. Edit again, type `sk-test-2222`, and Save. Read the hint.
  5. Open `http://127.0.0.1:8083/api/llm-profiles` and check no key appears.

### ST-05 A name already used
- **Who:** the person maintaining the Hub, adding a second model
- **Story:** As the maintainer, I want the Hub to stop two models from sharing a name, so that staff always know which model they pick in Chat.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - Adding a model named "Demo" (when "Demo" exists) keeps the dialog open, with "A profile with that name already exists." in red under Name. Every other field keeps its value.
  - Changing the name to "Demo 2" and saving works.
  - Renaming "Demo 2" to "Demo" with "Edit" shows the same error and keeps "Demo 2" unchanged.
- **Walk:**
  1. Click "Add AI model", choose "Demo (scripted)", type Name "Demo" and Model "scripted", and Save. Read the dialog.
  2. Change Name to "Demo 2" and Save.
  3. Click "Edit" on "Demo 2", change Name to "Demo", and Save. Read the dialog. Cancel, then delete "Demo 2".

### ST-06 Make another model the default
- **Who:** the GPSRC director switching the office to a new model
- **Story:** As the director, I want to choose which model Chat selects first, so that staff use the approved model unless they pick another.
- **Stack:** replay (Demo), with the helper profile "Demo B" (README)
- **Acceptance criteria:**
  - Only non-default cards show "Make default".
  - "Make default" on "Demo B" moves the "Default" tag to "Demo B". "Demo" now shows "Make default", and "Demo B" does not.
  - Chat in a browser that never picked a model (a private window) selects "Demo B".
  - A browser that picked a model in Chat before keeps its pick (CH-10).
- **Walk:**
  1. Create "Demo B" if needed. In Settings, click "Make default" on "Demo B". Read both cards.
  2. Open `/chat` in a private window and read "AI model".
  3. Click "Make default" on "Demo" to restore it.

### ST-07 Delete a model, the default, and the last one
- **Who:** the person maintaining the Hub, removing old models
- **Story:** As the maintainer, I want to delete models I no longer use, so that the list only holds what staff should pick, and the Hub always keeps a sensible default.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - "Delete" opens "Delete AI model" with 'Delete "<name>"? Its saved API key is removed too.' and "Cancel" and "Delete". "Cancel" keeps the model.
  - Deleting a non-default model removes its card, and Chat's "AI model" no longer lists it.
  - Deleting the default makes the oldest remaining model the default ("Default" tag).
  - Deleting the last model brings back "No AI models yet. Add one to start asking questions.", and Chat shows "Add an AI model in Settings to start.".
  - Conversations answered by a deleted model still open and show their answers.
- **Walk:**
  1. Create "Temp A" and "Temp B" (Provider "Demo (scripted)", Model "scripted"). In Chat, ask the CH-01 question with "Temp B".
  2. In Settings, click "Delete" on "Temp B", then "Cancel". Click "Delete" again, then "Delete". Check Chat's list, and reopen the conversation from step 1.
  3. Make "Temp A" the default, then delete it. Check which card is now "Default" ("Demo", the oldest).
  4. Delete every remaining model. Read Settings and Chat.
  5. Recreate "Demo" (README `curl`, or ST-01's form), then recreate "Unreachable" (see the top of this file).

### ST-08 Turn result sharing off
- **Who:** the GPSRC director after the sponsor decides a provider may not see personal data
- **Story:** As the director, I want to stop a model from ever receiving results, without any code change, so that the office follows the sponsor's decision at once.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - Editing "Demo" and turning off "Allow sending query results to this AI" removes the "Can receive results" tag from its card after Save.
  - Chat then shows the "Let AI see the results" switch off and greyed out for "Demo", with "This AI model isn't allowed to receive results. Change it in Settings." on hover, and answers carry no "AI-generated summary. Check it against the table." line.
  - Turning the setting back on restores the tag, and Chat's switch is enabled and on again.
- **Walk:**
  1. Click "Edit" on "Demo", turn the switch off, and Save. Read the card.
  2. In Chat, check the switch and its tooltip. Ask the CH-01 question and read the summary.
  3. Turn the setting back on in Settings. Check Chat's switch.

### ST-09 A base URL with a username and password
- **Who:** the person setting up a gateway that came with a URL holding credentials
- **Story:** As the person setting it up, I want the Hub to refuse a base URL that holds a username or password and tell me where the credential goes, so that the secret is never stored in a field the browser can read back.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - Saving Provider "Custom (OpenAI-compatible)", Name "Creds in URL", Base URL `https://user:secret@example.com/v1`, Model `test-model`, API key `sk-test` keeps the dialog open with an error, and no model is created.
  - The error says the base URL must not contain a username or password and that the credential belongs in the API key field, not a generic "Request validation failed" (expected; spec silent).
  - The error does not repeat the password.
  - Removing `user:secret@` and saving works.
- **Walk:**
  1. Click "Add AI model" and fill the fields as above. Click Save. Read the dialog and the list behind it.
  2. Change Base URL to `https://example.com/v1` and Save. Then delete "Creds in URL".

### ST-10 The app's secret key changed
- **Who:** the person maintaining the Hub after `HUB_SECRET_KEY` was replaced
- **Story:** As the maintainer, I want models whose saved keys can no longer be read to say so and be fixable by re-entering the key, so that a changed secret never fails silently.
- **Stack:** replay (Demo), api restarted with a new `HUB_SECRET_KEY`, with "Unreachable" from ST-03
- **Acceptance criteria:**
  - "Test" on "Unreachable" shows "The saved API key can't be read (the app's secret key changed). Re-enter the API key in Settings.".
  - Asking in Chat with "Unreachable" shows the same message, with "Retry". After a reload, the saved turn shows "The AI model has no usable API key. Re-enter it in Settings.".
  - "Demo" keeps working (it has no key).
  - Entering a new API key with "Edit" and saving makes "Test" reach the provider again ("Could not reach the AI provider. Check the base URL and your network, then retry.").
- **Walk:**
  1. Restart the api with a new secret key (README, "Restart the api with other limits", adding `HUB_SECRET_KEY=$(python3 -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())")`).
  2. In Settings, click "Test" on "Unreachable". Read the result.
  3. In Chat, choose "Unreachable" and ask the CH-01 question. Read the card, reload, and read it again. Choose "Demo" and ask again.
  4. Edit "Unreachable", type API key `sk-test-3333`, Save, and click "Test".
  5. Restart the api with the default limits (this brings back the `.env` secret), then delete "Unreachable".
