let intervalSequence = Date.now();
let hasUnsavedChanges = false;
let isSubmitting = false;


const form = document.querySelector("[data-schedule-form]");
const selectedWeekdayInput = document.querySelector(
    "[data-selected-weekday]"
);
const unsavedIndicator = document.querySelector(
    "[data-unsaved-indicator]"
);
const saveButton = document.querySelector("[data-save-button]");
const weekTotal = document.querySelector("[data-week-total]");
const reasonInput = document.querySelector("[data-change-reason]");
const reasonError = document.querySelector(
    "[data-change-reason-error]"
);
const reasonSection = document.querySelector(
    "[data-change-reason-section]"
);
const saveChangeDialog = document.querySelector(
    "[data-save-change-dialog]"
);
const saveChangeCancel = document.querySelector(
    "[data-save-change-cancel]"
);
const saveChangeConfirm = document.querySelector(
    "[data-save-change-confirm]"
);
const historyDrawer = document.querySelector(
    "[data-history-drawer]"
);
const historyOpenButton = document.querySelector(
    "[data-history-open]"
);
const historyCloseButton = document.querySelector(
    "[data-history-close]"
);
const audioInputs = Array.from(
    document.querySelectorAll('input[name="audio_file"]')
);
const audioPreviewButtons = Array.from(
    document.querySelectorAll("[data-audio-preview]")
);
const unsavedDialog = document.querySelector(
    "[data-unsaved-dialog]"
);
const unsavedDialogCancel = document.querySelector(
    "[data-unsaved-dialog-cancel]"
);
const unsavedDialogConfirm = document.querySelector(
    "[data-unsaved-dialog-confirm]"
);
const closeDayDialog = document.querySelector(
    "[data-close-day-dialog]"
);
const closeDayDialogCancel = document.querySelector(
    "[data-close-day-cancel]"
);
const closeDayDialogConfirm = document.querySelector(
    "[data-close-day-confirm]"
);
const closeDayTitle = document.querySelector(
    "[data-close-day-title]"
);
const closeDayDescription = document.querySelector(
    "[data-close-day-description]"
);
let pendingUnsavedAction = null;
let pendingClosePanel = null;
let dialogReturnFocus = null;
let activeAudio = null;
let activeAudioButton = null;


function timeToMinutes(value) {
    if (!value) {
        return null;
    }

    const parts = value.split(":");

    if (parts.length !== 2) {
        return null;
    }

    const minutes = (
        Number(parts[0]) * 60
        + Number(parts[1])
    );

    return Number.isNaN(minutes)
        ? null
        : minutes;
}


function minutesToDuration(minutes) {
    const hours = Math.floor(minutes / 60);
    const rest = minutes % 60;

    if (rest === 0) {
        return `${hours}h`;
    }

    return `${hours}h ${rest}m`;
}


function minutesToTime(minutes) {
    const safeMinutes = Math.max(
        0,
        Math.min(
            (23 * 60) + 59,
            minutes
        )
    );
    const hours = Math.floor(safeMinutes / 60);
    const rest = safeMinutes % 60;

    return [
        String(hours).padStart(2, "0"),
        String(rest).padStart(2, "0"),
    ].join(":");
}


function getPanelRows(panel) {
    return Array.from(
        panel.querySelectorAll("[data-interval-row]")
    );
}


function getRowTimes(row) {
    const startInput = row.querySelector(
        'input[name="start_time"]'
    );

    const endInput = row.querySelector(
        'input[name="end_time"]'
    );

    return {
        row,
        startInput,
        endInput,
        start: startInput ? startInput.value : "",
        end: endInput ? endInput.value : "",
        startMinutes: startInput
            ? timeToMinutes(startInput.value)
            : null,
        endMinutes: endInput
            ? timeToMinutes(endInput.value)
            : null,
    };
}


function getPanelRanges(panel) {
    return getPanelRows(panel)
        .map(getRowTimes)
        .filter(function (range) {
            return range.start && range.end;
        })
        .sort(function (first, second) {
            return first.startMinutes - second.startMinutes;
        });
}


function getValidPanelRanges(panel) {
    return getPanelRanges(panel).filter(function (range) {
        return (
            range.startMinutes !== null
            && range.endMinutes !== null
            && range.startMinutes < range.endMinutes
        );
    });
}


function getDayTab(weekday) {
    return document.querySelector(
        `[data-select-day][data-weekday="${weekday}"]`
    );
}


function getFocusableElements(container) {
    return Array.from(
        container.querySelectorAll(
            [
                "a[href]",
                "button:not([disabled])",
                "textarea:not([disabled])",
                "input:not([disabled])",
                "select:not([disabled])",
                "[tabindex]:not([tabindex='-1'])",
            ].join(", ")
        )
    );
}


function getOpenDialog() {
    return document.querySelector(
        ".schedule-dialog-backdrop:not([hidden])"
    );
}


function trapDialogFocus(event) {
    const openDialog = getOpenDialog();

    if (!openDialog || event.key !== "Tab") {
        return;
    }

    const focusableElements = getFocusableElements(openDialog);

    if (focusableElements.length === 0) {
        event.preventDefault();
        return;
    }

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[
        focusableElements.length - 1
    ];

    if (
        event.shiftKey
        && document.activeElement === firstElement
    ) {
        event.preventDefault();
        lastElement.focus();
        return;
    }

    if (
        !event.shiftKey
        && document.activeElement === lastElement
    ) {
        event.preventDefault();
        firstElement.focus();
    }
}


function restoreDialogFocus() {
    if (
        dialogReturnFocus
        && typeof dialogReturnFocus.focus === "function"
    ) {
        dialogReturnFocus.focus();
    }

    dialogReturnFocus = null;
}


function showUnsavedDialog(onConfirm) {
    if (!unsavedDialog) {
        onConfirm();
        return;
    }

    pendingUnsavedAction = onConfirm;
    dialogReturnFocus = document.activeElement;
    unsavedDialog.hidden = false;

    if (unsavedDialogCancel) {
        unsavedDialogCancel.focus();
    }
}


function closeUnsavedDialog() {
    if (!unsavedDialog) {
        return;
    }

    pendingUnsavedAction = null;
    unsavedDialog.hidden = true;
    restoreDialogFocus();
}


function confirmUnsavedDialog() {
    const action = pendingUnsavedAction;

    closeUnsavedDialog();

    if (action) {
        action();
    }
}


function showCloseDayDialog(panel) {
    if (!closeDayDialog) {
        replacePanelRanges(panel, []);
        markAsChanged();
        return;
    }

    pendingClosePanel = panel;
    dialogReturnFocus = document.activeElement;

    if (closeDayTitle) {
        closeDayTitle.textContent = (
            `Cerrar ${panel.dataset.dayLabel}`
        );
    }

    if (closeDayDescription) {
        closeDayDescription.textContent = (
            "Este día tiene horarios configurados. "
            + "¿Deseas marcarlo como cerrado y quitar esos horarios?"
        );
    }

    closeDayDialog.hidden = false;

    if (closeDayDialogCancel) {
        closeDayDialogCancel.focus();
    }
}


function closeCloseDayDialog() {
    if (!closeDayDialog) {
        return;
    }

    pendingClosePanel = null;
    closeDayDialog.hidden = true;
    restoreDialogFocus();
}


function confirmCloseDayDialog() {
    const panel = pendingClosePanel;

    closeCloseDayDialog();

    if (!panel) {
        return;
    }

    replacePanelRanges(panel, []);
    markAsChanged();
}


function showSaveChangeDialog() {
    if (!saveChangeDialog) {
        return;
    }

    dialogReturnFocus = document.activeElement;
    saveChangeDialog.hidden = false;
    updateSaveState();

    if (reasonInput) {
        reasonInput.focus();
    }
}


function closeSaveChangeDialog() {
    if (!saveChangeDialog) {
        return;
    }

    stopActiveAudio();
    saveChangeDialog.hidden = true;
    updateSaveState();
    restoreDialogFocus();
}


function showHistoryDrawer() {
    if (!historyDrawer) {
        return;
    }

    dialogReturnFocus = document.activeElement;
    historyDrawer.hidden = false;

    if (historyOpenButton) {
        historyOpenButton.setAttribute(
            "aria-expanded",
            "true"
        );
    }

    if (historyCloseButton) {
        historyCloseButton.focus();
    }
}


function closeHistoryDrawer() {
    if (!historyDrawer) {
        return;
    }

    historyDrawer.hidden = true;
    if (historyOpenButton) {
        historyOpenButton.setAttribute(
            "aria-expanded",
            "false"
        );
    }
    restoreDialogFocus();
}


function shouldConfirmNavigation(event, link) {
    const href = link.getAttribute("href");

    return (
        hasUnsavedChanges
        && !isSubmitting
        && href
        && !href.startsWith("#")
        && (!link.target || link.target === "_self")
        && !event.metaKey
        && !event.ctrlKey
        && !event.shiftKey
        && !event.altKey
    );
}


function setTabSummary(tabSummary, lines) {
    if (!tabSummary) {
        return;
    }

    tabSummary.textContent = "";

    lines.forEach(function (line) {
        const item = document.createElement("span");

        item.textContent = line;
        tabSummary.appendChild(item);
    });
}


function getSelectedAudioInput() {
    return audioInputs.find(function (input) {
        return input.checked;
    });
}


function getFirstAudioInput() {
    return audioInputs[0] || null;
}


function updateAudioValidity() {
    const firstAudioInput = getFirstAudioInput();

    if (!firstAudioInput) {
        return;
    }

    firstAudioInput.setCustomValidity("");
}


function validateRow(row) {
    const error = row.querySelector("[data-row-error]");
    const times = getRowTimes(row);

    if (!times.startInput || !times.endInput || !error) {
        return true;
    }

    if (!times.start || !times.end) {
        const message = "Completa la hora de apertura y cierre.";

        row.classList.add("has-error");
        error.textContent = message;

        if (!times.start) {
            times.startInput.setCustomValidity(message);
        } else {
            times.startInput.setCustomValidity("");
        }

        if (!times.end) {
            times.endInput.setCustomValidity(message);
        } else {
            times.endInput.setCustomValidity("");
        }

        return false;
    }

    if (
        times.startMinutes === null
        || times.endMinutes === null
        || times.startMinutes < times.endMinutes
    ) {
        times.startInput.setCustomValidity("");
        times.endInput.setCustomValidity("");
        row.classList.remove("has-error");
        error.textContent = "";

        return true;
    }

    const message = (
        "La hora de cierre debe ser posterior "
        + "a la hora de inicio."
    );

    times.startInput.setCustomValidity("");
    times.endInput.setCustomValidity(message);
    row.classList.add("has-error");
    error.textContent = message;

    return false;
}


function validatePanelOverlaps(panel) {
    const ranges = getPanelRanges(panel).filter(function (range) {
        return (
            range.startMinutes !== null
            && range.endMinutes !== null
            && range.startMinutes < range.endMinutes
        );
    });

    let hasOverlap = false;
    let activeRange = ranges[0] || null;

    ranges.slice(1).forEach(function (range) {
        if (!activeRange) {
            activeRange = range;
            return;
        }

        if (range.startMinutes < activeRange.endMinutes) {
            const message = (
                `El horario ${range.start}-${range.end} `
                + `se cruza con ${activeRange.start}-${activeRange.end}.`
            );
            const error = range.row.querySelector("[data-row-error]");

            range.row.classList.add("has-error");

            if (error) {
                error.textContent = message;
            }

            if (range.endInput) {
                range.endInput.setCustomValidity(message);
            }

            hasOverlap = true;
        }

        if (range.endMinutes > activeRange.endMinutes) {
            activeRange = range;
        }
    });

    return !hasOverlap;
}


function hasScheduleErrors() {
    let hasErrors = false;

    document
        .querySelectorAll("[data-interval-row]")
        .forEach(function (row) {
            if (!validateRow(row)) {
                hasErrors = true;
            }
        });

    document
        .querySelectorAll("[data-day-card]")
        .forEach(function (panel) {
            if (!validatePanelOverlaps(panel)) {
                hasErrors = true;
            }
        });

    return hasErrors;
}


function focusFirstScheduleError() {
    const firstErrorRow = document.querySelector(
        "[data-interval-row].has-error"
    );

    if (!firstErrorRow) {
        return;
    }

    const firstInvalidInput = firstErrorRow.querySelector(
        "input:invalid"
    ) || firstErrorRow.querySelector("input[type='time']");

    if (firstInvalidInput) {
        firstInvalidInput.focus();
    }
}


function updateSaveState() {
    if (!saveButton) {
        return;
    }

    const hasErrors = hasScheduleErrors();
    const reasonMissing = (
        reasonInput
        && !reasonInput.value.trim()
    );
    const reasonIsVisible = (
        reasonSection
        && !reasonSection.hidden
    );
    updateAudioValidity();

    if (reasonInput) {
        const shouldShowReasonError = (
            hasUnsavedChanges
            && reasonIsVisible
            && reasonMissing
        );

        reasonInput.setCustomValidity(
            shouldShowReasonError
                ? "El motivo es obligatorio."
                : ""
        );
        reasonInput.setAttribute(
            "aria-invalid",
            shouldShowReasonError ? "true" : "false"
        );
    }

    if (reasonError) {
        reasonError.textContent = (
            hasUnsavedChanges && reasonIsVisible && reasonMissing
                ? "El motivo es obligatorio."
                : ""
        );
    }

    if (unsavedIndicator && hasUnsavedChanges) {
        if (hasErrors) {
            unsavedIndicator.textContent = (
                "Corrige los horarios marcados"
            );
        } else if (reasonIsVisible && reasonMissing) {
            unsavedIndicator.textContent = (
                "Agrega un motivo para guardar"
            );
        } else {
            unsavedIndicator.textContent = (
                "Hay cambios sin guardar"
            );
        }
    }

    saveButton.disabled = (
        !hasUnsavedChanges
        || hasErrors
    );

    if (saveChangeConfirm) {
        saveChangeConfirm.disabled = (
            !hasUnsavedChanges
            || hasErrors
            || reasonMissing
        );
    }
}


function markAsChanged() {
    hasUnsavedChanges = true;

    if (unsavedIndicator) {
        unsavedIndicator.hidden = false;
        unsavedIndicator.classList.add("has-unsaved");
        unsavedIndicator.textContent = "Hay cambios sin guardar";
    }

    updateSaveState();
}


function setSubmittingState() {
    [
        saveButton,
        saveChangeConfirm,
    ].forEach(function (button) {
        if (!button) {
            return;
        }

        button.disabled = true;
        button.textContent = "Guardando...";
    });
}


function updateWeekTotal() {
    let totalMinutes = 0;

    document
        .querySelectorAll("[data-day-card]")
        .forEach(function (panel) {
            getValidPanelRanges(panel).forEach(function (range) {
                totalMinutes += (
                    range.endMinutes
                    - range.startMinutes
                );
            });
        });

    if (weekTotal) {
        weekTotal.textContent = minutesToDuration(
            totalMinutes
        );
    }
}


function updatePanelState(panel) {
    const rows = getPanelRows(panel);
    const isOpen = rows.length > 0;
    const weekday = panel.dataset.weekday;
    const tab = getDayTab(weekday);
    const addButton = panel.querySelector("[data-add-interval]");

    panel.classList.toggle("is-open", isOpen);
    panel.classList.toggle("is-closed", !isOpen);

    if (tab) {
        tab.classList.toggle("is-open", isOpen);
        tab.classList.toggle("is-closed", !isOpen);
    }

    panel
        .querySelectorAll("[data-set-day-state]")
        .forEach(function (button) {
            const shouldPress = (
                button.dataset.setDayState
                === (isOpen ? "open" : "closed")
            );

            button.setAttribute(
                "aria-pressed",
                shouldPress ? "true" : "false"
            );
        });

    if (addButton) {
        addButton.disabled = false;
        addButton.textContent = "+ Agregar horario";
        addButton.setAttribute(
            "aria-label",
            `Agregar horario para ${panel.dataset.dayLabel}`
        );
    }
}


function updatePanelText(panel) {
    const rows = getPanelRows(panel);
    const weekday = panel.dataset.weekday;
    const dayLabel = panel.dataset.dayLabel;
    const tab = getDayTab(weekday);
    const tabSummary = tab
        ? tab.querySelector("[data-day-tab-summary]")
        : null;
    const narrative = panel.querySelector(
        "[data-day-narrative]"
    );

    rows.forEach(function (row, index) {
        const removeButton = row.querySelector(
            "[data-remove-interval]"
        );

        if (removeButton) {
            removeButton.setAttribute(
                "aria-label",
                `Quitar horario ${index + 1} de ${dayLabel}`
            );
        }

        validateRow(row);
    });

    const ranges = getValidPanelRanges(panel);
    const hasOverlapErrors = !validatePanelOverlaps(panel);
    const hasInvalidRows = (
        hasOverlapErrors
        || rows.some(function (row) {
            return row.classList.contains("has-error");
        })
    );

    if (ranges.length === 0) {
        setTabSummary(
            tabSummary,
            [
                hasInvalidRows
                    ? "Revisar horario"
                    : "Cerrado",
            ]
        );

        if (narrative) {
            narrative.textContent = hasInvalidRows
                ? (
                    `Agrega al menos un horario para ${dayLabel} `
                    + "o marca el día como cerrado."
                )
                : "";
        }

        return;
    }

    const summary = ranges.map(function (range) {
        return `${range.start}-${range.end}`;
    });

    if (hasInvalidRows) {
        summary.push("Revisar");
    }

    setTabSummary(tabSummary, summary);

    if (!narrative) {
        return;
    }

    const parts = [];

    ranges.forEach(function (range, index) {
        parts.push(`de ${range.start} a ${range.end}`);

        const nextRange = ranges[index + 1];

        if (
            nextRange
            && range.endMinutes < nextRange.startMinutes
        ) {
            parts.push(
                `(Pausa de ${minutesToDuration(
                    nextRange.startMinutes - range.endMinutes
                )})`
            );
        }
    });

    narrative.textContent = (
        `${dayLabel}: `
        + parts.join(" y ")
        + (hasInvalidRows
            ? ". Corrige los horarios marcados."
            : ".")
    );
}


function updateEverything() {
    document
        .querySelectorAll("[data-day-card]")
        .forEach(function (panel) {
            updatePanelState(panel);
            updatePanelText(panel);
        });

    updateWeekTotal();
    updateSaveState();
}


function selectDay(weekday) {
    if (selectedWeekdayInput) {
        selectedWeekdayInput.value = weekday;
    }

    document
        .querySelectorAll("[data-day-card]")
        .forEach(function (panel) {
            panel.hidden = (
                panel.dataset.weekday !== weekday
            );
        });

    document
        .querySelectorAll("[data-select-day]")
        .forEach(function (tab) {
            const isSelected = (
                tab.dataset.weekday === weekday
            );

            tab.setAttribute(
                "aria-selected",
                isSelected ? "true" : "false"
            );
            tab.setAttribute(
                "aria-current",
                isSelected ? "true" : "false"
            );
        });
}


function createIntervalRow(
    weekday,
    dayLabel,
    start = "",
    end = "",
) {
    intervalSequence += 1;

    const intervalId = `${weekday}-${intervalSequence}`;
    const row = document.createElement("div");

    row.className = "interval-row";
    row.dataset.intervalRow = "";

    row.innerHTML = `
        <input
            type="hidden"
            name="weekday"
            value="${weekday}"
        >

        <div class="time-range">
            <div class="time-field">
                <label
                    class="sr-only"
                    for="start-${intervalId}"
                >
                    Inicio
                </label>

                <input
                    id="start-${intervalId}"
                    type="time"
                    name="start_time"
                    required
                    aria-label="Hora de apertura de nuevo horario de ${dayLabel}"
                >
            </div>

            <span
                class="time-arrow"
                aria-hidden="true"
            >
                →
            </span>

            <div class="time-field">
                <label
                    class="sr-only"
                    for="end-${intervalId}"
                >
                    Fin
                </label>

                <input
                    id="end-${intervalId}"
                    type="time"
                    name="end_time"
                    required
                    aria-label="Hora de cierre de nuevo horario de ${dayLabel}"
                >
            </div>

            <button
                type="button"
                class="remove-button"
                data-remove-interval
                aria-label="Quitar horario de ${dayLabel}"
            >
                <svg
                    aria-hidden="true"
                    viewBox="0 0 24 24"
                    focusable="false"
                >
                    <path d="M9 3h6l1 2h4v2H4V5h4l1-2Zm-2 6h10l-.7 11H7.7L7 9Zm3 2v7h2v-7h-2Zm4 0v7h2v-7h-2Z"></path>
                </svg>
            </button>
        </div>

        <p
            class="interval-error"
            data-row-error
            role="alert"
        ></p>
    `;

    const startInput = row.querySelector(
        'input[name="start_time"]'
    );
    const endInput = row.querySelector(
        'input[name="end_time"]'
    );

    startInput.value = start;
    endInput.value = end;

    return row;
}


function focusLastTimeRow(panel) {
    const newInput = panel.querySelector(
        ".interval-row:last-child input[type='time']"
    );

    if (newInput) {
        newInput.focus();
    }
}


function replacePanelRanges(panel, ranges) {
    const weekday = panel.dataset.weekday;
    const dayLabel = panel.dataset.dayLabel;
    const list = panel.querySelector(
        `[data-interval-list="${weekday}"]`
    );

    list.innerHTML = "";

    ranges.forEach(function (range) {
        list.appendChild(
            createIntervalRow(
                weekday,
                dayLabel,
                range[0],
                range[1]
            )
        );
    });

    updateEverything();
}


function setDayState(panel, state) {
    if (state === "closed") {
        const rows = getPanelRows(panel);

        if (rows.length > 0) {
            showCloseDayDialog(panel);
            return;
        }

        replacePanelRanges(panel, []);
        markAsChanged();
        return;
    }

    const ranges = getPanelRanges(panel);

    replacePanelRanges(
        panel,
        ranges.length > 0
            ? ranges.map(function (range) {
                return [range.start, range.end];
            })
            : [["", ""]]
    );

    markAsChanged();
    focusLastTimeRow(panel);
}


function addInterval(panel) {
    const weekday = panel.dataset.weekday;
    const dayLabel = panel.dataset.dayLabel;
    const list = panel.querySelector(
        `[data-interval-list="${weekday}"]`
    );
    const ranges = getValidPanelRanges(panel);
    const lastRange = ranges[ranges.length - 1];

    let start = "";
    let end = "";

    if (lastRange && lastRange.endMinutes < (23 * 60)) {
        start = lastRange.end;
        end = minutesToTime(lastRange.endMinutes + 60);
    }

    list.appendChild(
        createIntervalRow(
            weekday,
            dayLabel,
            start,
            end
        )
    );

    updateEverything();
    markAsChanged();

    focusLastTimeRow(panel);
}


document.addEventListener(
    "click",
    function (event) {
        const link = event.target.closest("a[href]");

        if (link && shouldConfirmNavigation(event, link)) {
            event.preventDefault();

            showUnsavedDialog(function () {
                isSubmitting = true;
                window.location.href = link.href;
            });

            return;
        }

        const dayTab = event.target.closest(
            "[data-select-day]"
        );

        if (dayTab) {
            selectDay(dayTab.dataset.weekday);
            return;
        }

        const stateButton = event.target.closest(
            "[data-set-day-state]"
        );

        if (stateButton) {
            setDayState(
                stateButton.closest("[data-day-card]"),
                stateButton.dataset.setDayState
            );
            return;
        }

        const addButton = event.target.closest(
            "[data-add-interval]"
        );

        if (addButton) {
            addInterval(
                addButton.closest("[data-day-card]")
            );
            return;
        }

        const removeButton = event.target.closest(
            "[data-remove-interval]"
        );

        if (removeButton) {
            const panel = removeButton.closest(
                "[data-day-card]"
            );

            removeButton
                .closest("[data-interval-row]")
                .remove();

            updateEverything();
            markAsChanged();
            return;
        }

        const audioChoiceCard = event.target.closest(
            ".audio-choice-card"
        );

        if (
            audioChoiceCard
            && !event.target.closest("[data-audio-preview]")
        ) {
            const input = audioChoiceCard.querySelector(
                'input[name="audio_file"]'
            );

            if (input && !input.checked) {
                input.checked = true;
                input.dispatchEvent(
                    new Event(
                        "change",
                        {
                            bubbles: true,
                        }
                    )
                );
            }
        }

    }
);


document.addEventListener(
    "submit",
    function (event) {
        const submittedForm = event.target;

        if (
            submittedForm === form
            || !hasUnsavedChanges
            || isSubmitting
        ) {
            return;
        }

        event.preventDefault();

        showUnsavedDialog(function () {
            isSubmitting = true;
            submittedForm.submit();
        });
    }
);


if (unsavedDialogCancel) {
    unsavedDialogCancel.addEventListener(
        "click",
        closeUnsavedDialog
    );
}


if (unsavedDialogConfirm) {
    unsavedDialogConfirm.addEventListener(
        "click",
        confirmUnsavedDialog
    );
}


if (closeDayDialogCancel) {
    closeDayDialogCancel.addEventListener(
        "click",
        closeCloseDayDialog
    );
}


if (closeDayDialogConfirm) {
    closeDayDialogConfirm.addEventListener(
        "click",
        confirmCloseDayDialog
    );
}


if (saveChangeCancel) {
    saveChangeCancel.addEventListener(
        "click",
        closeSaveChangeDialog
    );
}


if (historyOpenButton) {
    historyOpenButton.addEventListener(
        "click",
        showHistoryDrawer
    );
}


if (historyCloseButton) {
    historyCloseButton.addEventListener(
        "click",
        closeHistoryDrawer
    );
}


if (unsavedDialog) {
    unsavedDialog.addEventListener(
        "click",
        function (event) {
            if (event.target === unsavedDialog) {
                closeUnsavedDialog();
            }
        }
    );
}


if (closeDayDialog) {
    closeDayDialog.addEventListener(
        "click",
        function (event) {
            if (event.target === closeDayDialog) {
                closeCloseDayDialog();
            }
        }
    );
}


if (saveChangeDialog) {
    saveChangeDialog.addEventListener(
        "click",
        function (event) {
            if (event.target === saveChangeDialog) {
                closeSaveChangeDialog();
            }
        }
    );
}


if (historyDrawer) {
    historyDrawer.addEventListener(
        "click",
        function (event) {
            if (event.target === historyDrawer) {
                closeHistoryDrawer();
            }
        }
    );
}


document.addEventListener(
    "keydown",
    function (event) {
        trapDialogFocus(event);

        if (
            event.key === "Escape"
        ) {
            if (historyDrawer && !historyDrawer.hidden) {
                closeHistoryDrawer();
                return;
            }

            if (saveChangeDialog && !saveChangeDialog.hidden) {
                closeSaveChangeDialog();
                return;
            }

            if (closeDayDialog && !closeDayDialog.hidden) {
                closeCloseDayDialog();
                return;
            }

            if (unsavedDialog && !unsavedDialog.hidden) {
                closeUnsavedDialog();
            }
        }
    }
);


function stopActiveAudio() {
    if (activeAudio) {
        activeAudio.pause();
        activeAudio.currentTime = 0;
    }

    if (activeAudioButton) {
        activeAudioButton.textContent = "Escuchar ejemplo";
    }

    activeAudio = null;
    activeAudioButton = null;
}


audioPreviewButtons.forEach(function (button) {
    button.addEventListener(
        "click",
        function () {
            const audioSource = button.dataset.audioSrc;

            if (!audioSource) {
                return;
            }

            if (activeAudioButton === button && activeAudio) {
                stopActiveAudio();
                return;
            }

            stopActiveAudio();

            activeAudio = new Audio(audioSource);
            activeAudioButton = button;
            button.textContent = "Pausar";

            activeAudio.addEventListener(
                "ended",
                stopActiveAudio
            );

            activeAudio.play().catch(function () {
                button.textContent = "No disponible";
                activeAudio = null;
                activeAudioButton = null;
            });
        }
    );
});


if (form) {
    form.addEventListener(
        "input",
        function (event) {
            if (
                event.target.matches(
                    'input[name="start_time"], input[name="end_time"], textarea[name="change_reason"], input[name="audio_file"]'
                )
            ) {
                updateEverything();
                markAsChanged();
            }
        }
    );

    form.addEventListener(
        "change",
        function (event) {
            if (event.target.matches('input[name="audio_file"]')) {
                updateEverything();
                markAsChanged();
            }
        }
    );

    form.addEventListener(
        "submit",
        function (event) {
            const saveDialogIsOpen = (
                !saveChangeDialog
                || !saveChangeDialog.hidden
            );
            const reasonMissing = (
                reasonInput
                && !reasonInput.value.trim()
            );
            if (
                hasScheduleErrors()
            ) {
                event.preventDefault();
                updateSaveState();
                focusFirstScheduleError();
                return;
            }

            if (saveChangeDialog && !saveDialogIsOpen) {
                event.preventDefault();
                showSaveChangeDialog();
                return;
            }

            if (reasonMissing) {
                event.preventDefault();
                updateSaveState();

                if (reasonInput) {
                    if (reasonMissing) {
                        reasonInput.reportValidity();
                        reasonInput.focus();
                        return;
                    }
                }

                return;
            }

            isSubmitting = true;
            setSubmittingState();
        }
    );
}


window.addEventListener(
    "beforeunload",
    function (event) {
        if (
            !hasUnsavedChanges
            || isSubmitting
        ) {
            return;
        }

        event.preventDefault();
        event.returnValue = "";
    }
);


const firstOpenPanel = document.querySelector(
    "[data-day-card].is-open"
);
const firstPanel = document.querySelector("[data-day-card]");
const errorSummary = document.querySelector("#schedule-errors");
const initialWeekday = (
    form
    && form.dataset.initialWeekday
);
const initialPanel = initialWeekday
    ? document.querySelector(
        `[data-day-card][data-weekday="${initialWeekday}"]`
    )
    : null;

updateEverything();

if (initialPanel || firstOpenPanel || firstPanel) {
    selectDay(
        (initialPanel || firstOpenPanel || firstPanel).dataset.weekday
    );
}

if (errorSummary) {
    errorSummary.focus();
}
