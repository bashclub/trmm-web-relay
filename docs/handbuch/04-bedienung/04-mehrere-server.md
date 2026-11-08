---
title: Mehrere TRMM-Server
audience: Anwender, Admin
outline:
outline_id:
---
Ein Client kann mehrere TRMM-Server kennen, z. B. die Instanz des eigenen MSP und die eines Partners, oder eine Test- und eine Produktivinstanz. Jeder Server hat seinen eigenen Sprung-Host, API-Key und seine eigene CA.

## Ein Server zur Zeit
Die Steuerseite zeigt immer nur die Sites **eines** Servers. Damit arbeitet man bewusst in einer Instanz und landet nicht versehentlich beim falschen Kunden. Sind mehrere eingerichtet, steht oben eine Auswahl. Die Wahl bleibt gespeichert (`active_server`) und gilt auch nach einem Neustart.

**Umschalten beendet alle offenen Verbindungen**, nach Rückfrage, wenn welche offen sind. Danach lädt der Client die Sites des neuen Servers.

## Einen Server hinzufügen
In der **Einrichtung** **Server hinzufügen** und die Schritte wie beim ersten Server durchgehen ([Einrichtung im Client](../03-installation/04-einrichtung.md)). Für einen fremden TRMM gilt: Felder und Skripte legt einmal jemand mit Schreibrechten an; der eigene Key braucht nur die Leserechte und `Run Scripts`. Den Installer bzw. die CA-Zeile bekommt der Betreiber des Sprung-Hosts dieser Instanz.

## Kommandozeile
`trmm-web-relay check` und `trmm-web-relay targets` arbeiten über alle Server, unabhängig vom aktiven.
